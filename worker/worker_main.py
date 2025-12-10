import time
import os
import io
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
from uuid import uuid4
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load env vars
env_path = ".env"
if not os.path.exists(env_path):
    # Try looking in backend folder (sibling)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env")

print(f"Loading env from: {env_path}")
load_dotenv(env_path)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for worker

# Graceful exit or error if env vars missing
if not url or not key:
    print("WARNING: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file for worker to function.")

try:
    supabase: Client = create_client(url, key) if url and key else None
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

# Initialize models (loading global to avoid reloading per task)
print("Loading models...")
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    print("Models loaded.")
except Exception as e:
    print(f"Error loading models: {e}")
    # In a real scenario we might exit, but here we keep running to avoid crash loops
    embedding_model = None
    text_splitter = None

def process_document(doc):
    if not supabase or not embedding_model:
        print("Worker not fully initialized (Supabase or Models missing). Skipping process.")
        time.sleep(10)
        return

    try:
        doc_id = doc['id']
        file_url = doc['file_url']
        print(f"Processing document {doc_id}...")

        # Update status to processing
        supabase.table("documents").update({"status": "processing"}).eq("id", doc_id).execute()

        # Download file
        # Note: file_url might be a public URL or Signed URL.
        # If it's a public URL we can use requests.
        response = requests.get(file_url)
        response.raise_for_status()
        file_content = response.content
        
        # Extract Text
        content = ""
        filename = doc['filename'].lower()
        if filename.endswith(".pdf"):
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        else:
            content = file_content.decode("utf-8")

        # Chunk
        chunks = text_splitter.split_text(content)
        
        # Embed
        embeddings = embedding_model.encode(chunks)
        
        # Save chunks
        records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            records.append({
                "document_id": doc_id,
                "content": chunk,
                "embedding": embedding.tolist(),
                "chunk_index": i
            })
        
        if records:
            supabase.table("document_chunks").insert(records).execute()
        
        # Update status to ready
        supabase.table("documents").update({
            "status": "ready", 
            "processed": True,
            "error_message": None
        }).eq("id", doc_id).execute()
        
        print(f"Document {doc_id} processed successfully.")

    except Exception as e:
        print(f"Error processing document {doc['id']}: {e}")
        supabase.table("documents").update({
            "status": "failed", 
            "error_message": str(e)
        }).eq("id", doc['id']).execute()

def main():
    print("Worker started. Polling for pending documents...")
    while True:
        try:
            if not supabase:
                print("Supabase client not initialized. Retrying in 10s...")
                time.sleep(10)
                continue

            # Fetch pending documents
            response = supabase.table("documents").select("*").eq("status", "pending").execute()
            docs = response.data
            
            if docs:
                print(f"Found {len(docs)} pending documents.")
                for doc in docs:
                    process_document(doc)
            else:
                # Sleep if no docs
                time.sleep(5)
                
        except Exception as e:
            print(f"Error in polling loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
