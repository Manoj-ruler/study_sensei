from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import supabase
from rag import rag_service
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Optional, Any
import requests
import json
import os
import re

router = APIRouter(prefix="/solver", tags=["solver"])

# Initialize Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

class GenerateQuestionRequest(BaseModel):
    skill_id: str
    topic: str
    difficulty: str = "Medium" # Easy, Medium, Hard

class SubmitCodeRequest(BaseModel):
    user_id: str
    question_id: str
    code: str
    language: str = "python"

@router.post("/generate-question")
async def generate_question(payload: GenerateQuestionRequest):
    try:
        # 1. RAG Context (Optional but helpful)
        query_embedding = rag_service.model.encode(payload.topic).tolist()
        params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.3,
            "match_count": 3,
            "filter_skill_id": payload.skill_id
        }
        # Assuming match_documents RPC exists and works (reusing from chat)
        try:
            response = supabase.rpc("match_documents", params).execute()
            matches = response.data
            context_text = "\n\n".join([match['content'] for match in matches]) if matches else ""
        except:
            context_text = ""

        # 2. Prompt LLM
        system_prompt = """You are an expert coding interviewer. Generate a coding problem based on the provided topic and context.
        Output MUST be valid JSON with the following structure:
        {
            "title": "Problem Title",
            "description": "Markown description of the problem",
            "difficulty": "Easy/Medium/Hard",
            "test_cases": [
                {"input": "1 2", "expected_output": "3", "is_hidden": false},
                {"input": "5 5", "expected_output": "10", "is_hidden": true}
            ]
        }
        Ensure test_cases cover edge cases. Input should be string format expected by standard input (stdin).
        Expected output should be the exact string printed to stdout.
        """
        
        user_prompt = f"Topic: {payload.topic}\nDifficulty: {payload.difficulty}\nContext: {context_text}"
        
        # Invoke LLM
        ai_response = llm.invoke(f"{system_prompt}\n\n{user_prompt}")
        content = ai_response.content
        print(f"DEBUG: Raw content type: {type(content)}")
        print(f"DEBUG: Raw content: {content}")
        
        if not isinstance(content, str):
            if isinstance(content, list):
                # Handle list of content blocks (e.g. [{'type': 'text', 'text': '...'}])
                extracted = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        extracted.append(part['text'])
                    elif isinstance(part, str):
                        extracted.append(part)
                content = "".join(extracted)
            elif hasattr(content, 'parts'):
                 # Handle case where content might be a list of parts (Gemini specific)
                 content = "".join([part.text for part in content.parts])
            else:
                content = str(content)

        # Clean JSON (Gemini sometimes wraps in ```json ... ```)
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*$", "", content)
        content = content.strip()
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {content}")
            raise HTTPException(status_code=500, detail="AI generated invalid JSON")

        # 3. Save to DB
        # Save Question
        q_data = {
            "skill_id": payload.skill_id,
            "title": data.get("title", "Untitled Problem"),
            "description": data.get("description", "No description"),
            "difficulty": data.get("difficulty", payload.difficulty)
        }
        q_res = supabase.table("coding_questions").insert(q_data).execute()
        question_id = q_res.data[0]['id']
        
        # Save Test Cases
        test_cases = data.get("test_cases", [])
        tc_records = []
        for tc in test_cases:
            tc_records.append({
                "question_id": question_id,
                "input": tc.get("input", ""),
                "expected_output": tc.get("expected_output", ""),
                "is_hidden": tc.get("is_hidden", False)
            })
        
        if tc_records:
            supabase.table("test_cases").insert(tc_records).execute()
            
        return {
            "status": "success",
            "question": {
                "id": question_id,
                **q_data,
                "test_cases": tc_records
            }
        }

    except Exception as e:
        print(f"Generate Question Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit")
async def submit_code(payload: SubmitCodeRequest):
    try:
        # 1. Fetch Test Cases
        tc_res = supabase.table("test_cases").select("*").eq("question_id", payload.question_id).execute()
        test_cases = tc_res.data
        
        if not test_cases:
            raise HTTPException(status_code=404, detail="No test cases found for this question")
            
        # 2. Run Code against Test Cases
        results = []
        passed_count = 0
        overall_status = "passed"
        
        CODE_RUNNER_URL = os.environ.get("CODE_RUNNER_URL", "http://code_runner:8001/run")
        
        for tc in test_cases:
            try:
                # Call Code Runner Service
                response = requests.post(CODE_RUNNER_URL, json={
                    "code": payload.code,
                    "input_data": tc['input'],
                    "language": payload.language
                }, timeout=10)
                
                if response.status_code != 200:
                    res_data = {"status": "error", "output": "Runner Error"}
                else:
                    res_data = response.json()
                
                actual_output = res_data.get("output", "").strip()
                expected = tc['expected_output'].strip()
                
                # Normalize whitespace: replace all whitespace sequences with single space
                actual_normalized = re.sub(r'\s+', ' ', actual_output).strip()
                expected_normalized = re.sub(r'\s+', ' ', expected).strip()
                
                passed = actual_normalized == expected_normalized
                
                if not passed:
                    print(f"DEBUG: Comparison Failed")
                    print(f"Expected (raw): {repr(expected)}")
                    print(f"Actual (raw):   {repr(actual_output)}")
                    print(f"Expected (norm): {repr(expected_normalized)}")
                    print(f"Actual (norm):   {repr(actual_normalized)}")

                if passed:
                    passed_count += 1
                else:
                    overall_status = "failed"
                
                results.append({
                    "input": tc['input'],
                    "expected": expected,
                    "actual": actual_output,
                    "passed": passed,
                    "is_hidden": tc['is_hidden']
                })
                
            except Exception as e:
                print(f"Runner call failed: {e}")
                overall_status = "error"
                results.append({
                    "input": tc['input'],
                    "error": str(e),
                    "passed": False,
                    "is_hidden": tc['is_hidden']
                })
        
        # 3. Save Submission
        sub_data = {
            "user_id": payload.user_id,
            "question_id": payload.question_id,
            "code": payload.code,
            "language": payload.language,
            "status": overall_status,
            "output": json.dumps(results) # Store detailed results
        }
        supabase.table("code_submissions").insert(sub_data).execute()
        
        # 4. Log to Analytics (Progress Metrics)
        try:
            # Fetch skill_id for this question
            q_info = supabase.table("coding_questions").select("skill_id").eq("id", payload.question_id).single().execute()
            skill_id = q_info.data['skill_id'] if q_info.data else None
            
            if skill_id:
                analytics_data = {
                    "user_id": payload.user_id,
                    "skill_id": skill_id,
                    "activity_type": "code",
                    "score": passed_count,
                    "max_score": len(test_cases),
                    "metadata": {
                        "passed": overall_status == "passed",
                        "question_id": payload.question_id,
                        "language": payload.language
                    }
                }
                supabase.table("progress_metrics").insert(analytics_data).execute()
        except Exception as log_error:
            print(f"Failed to log analytics: {log_error}")

        return {
            "status": overall_status,
            "passed_count": passed_count,
            "total_count": len(test_cases),
            "results": results 
        }

    except Exception as e:
        print(f"Submit Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
