from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import supabase
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re
import os

router = APIRouter(prefix="/quiz", tags=["quiz"])

class QuizRequest(BaseModel):
    skill_id: str
    topic: Optional[str] = None
    num_questions: int = 5

class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

class QuizResponse(BaseModel):
    questions: List[Question]

# Initialize Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

class QuestionResult(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    user_answer: int
    is_correct: bool

class QuizResult(BaseModel):
    skill_id: str
    user_id: str
    score: int
    total_questions: int
    questions: List[QuestionResult]

@router.post("/save")
async def save_quiz(payload: QuizResult):
    try:
        # 1. Save Quiz Summary
        data = {
            "skill_id": payload.skill_id,
            "score": payload.score,
            "total_questions": payload.total_questions
        }
        quiz_res = supabase.table("quizzes").insert(data).execute()
        quiz_id = quiz_res.data[0]['id']

        # 2. Save Questions
        questions_data = []
        for q in payload.questions:
            questions_data.append({
                "quiz_id": quiz_id,
                "skill_id": payload.skill_id,
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "user_answer": q.user_answer,
                "is_correct": q.is_correct
            })
        
        if questions_data:
            supabase.table("quiz_questions").insert(questions_data).execute()

        # 3. Log to Analytics (Progress Metrics)
        analytics_data = {
            "user_id": payload.user_id,
            "skill_id": payload.skill_id,
            "activity_type": "quiz",
            "score": payload.score,
            "max_score": payload.total_questions,
            "metadata": {"total_questions": payload.total_questions}
        }
        supabase.table("progress_metrics").insert(analytics_data).execute()

        return {"status": "success", "message": "Quiz result saved"}
    except Exception as e:
        print(f"Save Quiz Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(payload: QuizRequest):
    try:
        # 1. Fetch random chunks
        response = supabase.table("documents") \
            .select("id") \
            .eq("skill_id", payload.skill_id) \
            .execute()
        
        doc_ids = [d['id'] for d in response.data]
        
        if not doc_ids:
            raise HTTPException(status_code=404, detail="No documents found for this skill")

        chunks_response = supabase.table("document_chunks") \
            .select("content") \
            .in_("document_id", doc_ids) \
            .limit(10) \
            .execute()
            
        context = "\n".join([c['content'] for c in chunks_response.data])
        
        # 2. Fetch previous questions to avoid repetition
        # Get last 20 questions for this skill
        prev_questions_res = supabase.table("quiz_questions") \
            .select("question") \
            .eq("skill_id", payload.skill_id) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
            
        prev_questions = [q['question'] for q in prev_questions_res.data]
        
        # 3. Prompt LLM
        prompt = f"""
        You are a teacher. Create a quiz with {payload.num_questions} multiple-choice questions based on the following text.
        
        Text:
        {context[:3000]}... (truncated)
        
        IMPORTANT: Do NOT generate questions similar to these (they were already asked):
        {json.dumps(prev_questions)}
        
        Return ONLY a raw JSON array. Do not use Markdown formatting.
        Format:
        [
            {{
                "question": "Question text",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0, // Index of correct option (0-3)
                "explanation": "Why it is correct"
            }}
        ]
        """
        
        ai_response = llm.invoke(prompt)
        
        # 3. Clean and Parse JSON
        # Sometimes LLMs add ```json ... ```
        cleaned_json = re.sub(r'```json\s*|\s*```', '', ai_response.content).strip()
        
        questions_data = json.loads(cleaned_json)
        
        # Shuffle options to prevent correct answer always being at index 0
        import random
        for question in questions_data:
            # Create list of (option, is_correct) tuples
            options_with_correctness = [
                (opt, idx == question['correct_answer']) 
                for idx, opt in enumerate(question['options'])
            ]
            
            # Shuffle the options
            random.shuffle(options_with_correctness)
            
            # Rebuild options list and find new correct answer index
            question['options'] = [opt for opt, _ in options_with_correctness]
            question['correct_answer'] = next(
                idx for idx, (_, is_correct) in enumerate(options_with_correctness) 
                if is_correct
            )
        
        return {"questions": questions_data}

    except json.JSONDecodeError:
        print(f"JSON Error. Raw AI response: {ai_response}")
        raise HTTPException(status_code=500, detail="Failed to generate valid quiz JSON")
    except Exception as e:
        print(f"Quiz Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{skill_id}")
async def get_quiz_history(skill_id: str):
    try:
        # Fetch quizzes for this skill with their questions
        quizzes_response = supabase.table("quizzes") \
            .select("*") \
            .eq("skill_id", skill_id) \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()
        
        quizzes = []
        for quiz in quizzes_response.data:
            # Fetch questions for this quiz
            questions_response = supabase.table("quiz_questions") \
                .select("*") \
                .eq("quiz_id", quiz['id']) \
                .execute()
            
            quiz['questions'] = questions_response.data
            quizzes.append(quiz)
        
        return {"quizzes": quizzes}
    except Exception as e:
        print(f"Quiz History Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
