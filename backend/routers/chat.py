from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import supabase
from rag import rag_service
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Optional
import os

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    chat_id: Optional[str] = None
    user_id: str # In production, get from auth
    message: str
    skill_id: Optional[str] = None
    mode: Optional[str] = "chat"

# Initialize Gemini
# Ensure GOOGLE_API_KEY is set in .env
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

@router.post("/message")
async def chat_message(payload: ChatMessage):
    try:
        # 0. Ensure Chat ID exists
        chat_id = payload.chat_id
        if not chat_id:
            # Create new chat
            chat_data = {
                "user_id": payload.user_id,
                "skill_id": payload.skill_id,
                "title": payload.message[:50] + "..." if len(payload.message) > 50 else payload.message
            }
            chat_res = supabase.table("chats").insert(chat_data).execute()
            chat_id = chat_res.data[0]['id']

        # 1. Generate embedding for the user query
        query_embedding = rag_service.model.encode(payload.message).tolist()
        
        # 2. Search for relevant chunks in Supabase
        # We use the RPC function 'match_documents' we defined in SQL
        params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.3, # Lowered threshold for better recall
            "match_count": 5,
            "filter_skill_id": payload.skill_id
        }
        response = supabase.rpc("match_documents", params).execute()
        matches = response.data
        
        print(f"RAG Matches found: {len(matches)}") # Debug log
        
        # 3. Construct Context
        context_text = "\n\n".join([match['content'] for match in matches])
        
        # 3.5 Fetch Chat History
        history_text = ""
        if chat_id:
            recent_messages = supabase.table("messages") \
                .select("role, content") \
                .eq("chat_id", chat_id) \
                .order("created_at", desc=True) \
                .limit(10) \
                .execute()
            
            # Reverse to get chronological order
            for msg in reversed(recent_messages.data):
                role = "Student" if msg['role'] == "user" else "Teacher"
                history_text += f"{role}: {msg['content']}\n"

        # 4. Construct Prompt
        system_prompt = """You are StudySensei, an AI tutor. Use the following context to answer the student's question. 
        If the answer is not in the context, say you don't know but try to be helpful based on general knowledge.
        Keep answers concise and encouraging."""
        
        full_prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nConversation History:\n{history_text}\nStudent: {payload.message}\nTeacher:"
        
        # 5. Generate Answer with LLM
        # For streaming, we'd use StreamingResponse, but for MVP simple return
        ai_response = llm.invoke(full_prompt)
        
        # Helper to ensure content is string
        content = ai_response.content
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
        
        # 6. Save Chat History
        # Save User Message
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": "user",
            "content": payload.message,
            "mode": payload.mode
        }).execute()
        
        # Save AI Message
        supabase.table("messages").insert({
            "chat_id": chat_id,
            "role": "assistant",
            "content": content,
            "mode": payload.mode
        }).execute()
        
        return {
            "chat_id": chat_id,
            "response": content,
            "sources": matches
        }

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    try:
        # 1. Delete messages
        supabase.table("messages").delete().eq("chat_id", chat_id).execute()
        
        # 2. Delete chat
        supabase.table("chats").delete().eq("id", chat_id).execute()
        
        return {"status": "success", "message": "Chat deleted"}
    except Exception as e:
        print(f"Delete Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
