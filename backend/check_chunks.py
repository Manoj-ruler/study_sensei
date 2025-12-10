from database import supabase

try:
    # Get latest document
    print("Fetching latest document...")
    docs = supabase.table("documents").select("*").order("created_at", desc=True).limit(1).execute()
    
    if not docs.data:
        print("No documents found.")
        exit()
        
    doc = docs.data[0]
    print(f"Latest Document: {doc['filename']} (ID: {doc['id']})")
    print(f"Processed: {doc['processed']}")
    
    # Check chunks
    print(f"Fetching chunks for document {doc['id']}...")
    chunks = supabase.table("document_chunks").select("id, content, chunk_index").eq("document_id", doc['id']).execute()
    
    print(f"Found {len(chunks.data)} chunks.")
    if chunks.data:
        print("Sample chunk content:")
        print(chunks.data[0]['content'][:100] + "...")
        
except Exception as e:
    print(f"Error: {e}")
