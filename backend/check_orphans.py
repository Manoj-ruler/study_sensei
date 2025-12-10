from database import supabase

try:
    print("Checking for orphaned chunks...")
    
    # Get all document IDs
    docs = supabase.table("documents").select("id").execute()
    doc_ids = set(d['id'] for d in docs.data)
    print(f"Active Document IDs: {len(doc_ids)}")
    
    # Get all chunk document_ids (this might be large, so we'll just get a sample or count)
    # Ideally we'd do a left join in SQL, but for now let's just check a few
    chunks = supabase.table("document_chunks").select("document_id").execute()
    
    orphans = 0
    for chunk in chunks.data:
        if chunk['document_id'] not in doc_ids:
            orphans += 1
            
    print(f"Total Chunks: {len(chunks.data)}")
    print(f"Orphaned Chunks: {orphans}")
    
    if orphans > 0:
        print("ISSUE CONFIRMED: Chunks exist for deleted documents.")

except Exception as e:
    print(f"Error: {e}")
