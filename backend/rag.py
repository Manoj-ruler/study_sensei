from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from database import supabase
import uuid

class RAGService:
    def __init__(self):
        # Initialize the embedding model
        # all-MiniLM-L6-v2 creates 384-dimensional vectors
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def process_document(self, document_id: str, content: str):
        """
        Splits content into chunks, generates embeddings, and stores them in Supabase.
        """
        try:
            # 1. Split text into chunks
            chunks = self.text_splitter.split_text(content)
            
            # 2. Generate embeddings for all chunks
            embeddings = self.model.encode(chunks)
            
            # 3. Prepare data for insertion
            records = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                records.append({
                    "document_id": document_id,
                    "content": chunk,
                    "embedding": embedding.tolist(),
                    "chunk_index": i
                })
            
            # 4. Insert into Supabase
            if records:
                supabase.table("document_chunks").insert(records).execute()
            
            # 5. Mark document as processed
            supabase.table("documents").update({"processed": True}).eq("id", document_id).execute()
            
            return True
        except Exception as e:
            print(f"Error processing document {document_id}: {e}")
            return False

# Singleton instance
rag_service = RAGService()
