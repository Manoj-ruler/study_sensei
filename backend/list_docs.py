from database import supabase

try:
    print("Listing active documents...")
    docs = supabase.table("documents").select("id, filename, created_at").execute()
    
    for doc in docs.data:
        print(f"- {doc['filename']} (ID: {doc['id']})")
        
except Exception as e:
    print(f"Error: {e}")
