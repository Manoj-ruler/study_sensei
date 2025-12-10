from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
import shutil
import os
from uuid import uuid4
from database import supabase

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    skill_id: str = Form(...),
    user_id: str = Form(...)
):
    try:
        # 1. Read file content
        file_content = await file.read()
        
        # 2. Upload to Supabase Storage
        file_ext = file.filename.split(".")[-1]
        storage_path = f"{user_id}/{skill_id}/{uuid4()}.{file_ext}"
        
        try:
            supabase.storage.from_("documents").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": file.content_type}
            )
        except Exception as e:
            print(f"Supabase Storage upload failed (ensure 'documents' bucket exists): {e}")

        # 3. Save metadata to DB (skip extraction and processing)
        # Get public URL if possible, otherwise use storage path
        try:
            public_url = supabase.storage.from_("documents").get_public_url(storage_path)
        except:
            public_url = storage_path

        data = {
            "user_id": user_id,
            "skill_id": skill_id,
            "filename": file.filename,
            "file_url": public_url,
            "processed": False,
            "status": "pending",
            "error_message": None
        }
        response = supabase.table("documents").insert(data).execute()
        document_id = response.data[0]['id']

        # Processing will be picked up by the background worker monitoring 'pending' status

        return {"status": "success", "document_id": document_id, "message": "File uploaded. Processing started in background."}

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    try:
        # 1. Get document to find storage path
        doc = supabase.table("documents").select("*").eq("id", document_id).single().execute()
        if not doc.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_url = doc.data['file_url']
        
        # 2. Delete from Storage
        # Extract path from URL: .../documents/path/to/file
        if "/documents/" in file_url:
            storage_path = file_url.split("/documents/")[-1]
            supabase.storage.from_("documents").remove([storage_path])
        
        # 3. Delete from DB
        # Explicitly delete chunks first to ensure no orphans (even if cascade is missing)
        supabase.table("document_chunks").delete().eq("document_id", document_id).execute()
        
        # Then delete the document
        supabase.table("documents").delete().eq("id", document_id).execute()
        
        return {"status": "success", "message": "Document deleted"}
        
    except Exception as e:
        print(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
