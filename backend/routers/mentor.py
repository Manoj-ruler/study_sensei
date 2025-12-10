from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import supabase
from rag import rag_service
from langchain_google_genai import ChatGoogleGenerativeAI
import json

router = APIRouter(prefix="/mentor", tags=["mentor"])

# Initialize Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

class MentorMessage(BaseModel):
    user_id: str
    skill_id: str
    chat_id: Optional[str] = None
    message: str
    mode: str = "explain" # explain, quiz, plan, coach

@router.post("/message")
async def mentor_message(payload: MentorMessage):
    try:
        # 0. Ensure Chat ID exists
        chat_id = payload.chat_id
        if not chat_id:
            chat_data = {
                "user_id": payload.user_id,
                "skill_id": payload.skill_id,
                "title": f"[{payload.mode.upper()}] " + (payload.message[:30] + "..." if len(payload.message) > 30 else payload.message)
            }
            chat_res = supabase.table("chats").insert(chat_data).execute()
            chat_id = chat_res.data[0]['id']

        # 1. Fetch Context (RAG) - Common for Explain, Quiz, Plan
        # Coach might not need deep RAG, but context helps personalization.
        context_text = ""
        sources = []
        
        if payload.mode in ["explain", "quiz", "plan"]:
            query_embedding = rag_service.model.encode(payload.message).tolist()
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.3, 
                "match_count": 5,
                "filter_skill_id": payload.skill_id
            }
            try:
                response = supabase.rpc("match_documents", params).execute()
                sources = response.data
                context_text = "\n\n".join([match['content'] for match in sources])
            except Exception as e:
                print(f"RAG Error: {e}")

        # 1.5 Fallback for Quiz: If Context is empty, fetch random chunks from the skill
        # This prevents "random trivia" when the user just says "give me a quiz"
        if payload.mode == "quiz" and not context_text:
            try:
                # Get documents for this skill
                doc_res = supabase.table("documents").select("id").eq("skill_id", payload.skill_id).execute()
                doc_ids = [d['id'] for d in doc_res.data]
                
                if doc_ids:
                    # Fetch random chunks (limit 5)
                    chunk_res = supabase.table("document_chunks") \
                        .select("content") \
                        .in_("document_id", doc_ids) \
                        .limit(5) \
                        .execute()
                    
                    if chunk_res.data:
                        print("Using fallback context for quiz.")
                        sources = [{"content": c['content']} for c in chunk_res.data]
                        context_text = "\n\n".join([c['content'] for c in sources])
            except Exception as e:
                print(f"Fallback Context Error: {e}")

        # 2. Select Agent / Prompt
        system_prompt = ""
        
        if payload.mode == "explain":
            system_prompt = """You are the 'Deep Explainer' agent. 
            Goal: Explain concepts clearly, using analogies and simple terms. 
            Use the provided context to ground your explanation. 
            If the context is insufficient, rely on your general knowledge but mention that it's general info.
            Style: Educational, patient, clear."""
        
        elif payload.mode == "quiz":
            system_prompt = """You are the 'Examiner' agent.
            Goal: Generate a mini-quiz (3 questions) based on the user's request and provided context.
            Output Format: JSON ONLY.
            Structure: 
            [
                { "question": "...", "options": ["a", "b", "c", "d"], "answer": "correct option content", "explanation": "..." },
                ...
            ]
            Do not include any conversational text outside the JSON."""
        
        elif payload.mode == "plan":
            system_prompt = """You are the 'Study Architect' agent.
            Goal: Create a structured study plan based on the user's goal and available materials (context).
            Output: Markdown formatted plan with days/steps.
            Style: Structured, actionable, motivating."""
            
        elif payload.mode == "coach":
            system_prompt = """You are the 'Motivator' agent.
            Goal: Encourage the student, help them overcome procrastination or frustration.
            Style: High energy, empathetic, inspiring. Short and punchy."""
        
        else:
            # Fallback
            system_prompt = "You are a helpful AI tutor."

        # 3. Generate Response
        full_prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nUser Request: {payload.message}\nAgent Response:"
        
        ai_response = llm.invoke(full_prompt)
        content = ai_response.content
        
        # Helper to ensure content is string (Gemini sometimes returns complex objects)
        if not isinstance(content, str):
            if isinstance(content, list):
                extracted = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        extracted.append(part['text'])
                    elif isinstance(part, str):
                        extracted.append(part)
                content = "".join(extracted)
            elif hasattr(content, 'parts'):
                 content = "".join([part.text for part in content.parts])
            else:
                content = str(content)
        
        # Post-processing for Quiz
        if payload.mode == "quiz":
            # Clean JSON
            import re
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```\s*$", "", content)
            content = content.strip()

        # 4. Save History
        # User Msg
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": "user",
            "content": payload.message,
            "mode": payload.mode
        }).execute()
        
        # AI Msg
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": "assistant",
            "content": content,
            "mode": payload.mode
        }).execute()

        return {
            "chat_id": chat_id,
            "response": content,
            "mode": payload.mode,
            "sources": sources
        }

    except Exception as e:
        print(f"Mentor Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
