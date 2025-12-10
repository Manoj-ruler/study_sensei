from database import supabase

try:
    print("Checking 'documents' table...")
    docs = supabase.table("documents").select("*").limit(1).execute()
    print(f"Documents columns: {docs.data[0].keys() if docs.data else 'Table empty or no access'}")
    if docs.data:
        print(f"Sample URL: {docs.data[0]['file_url']}")
except Exception as e:
    print(f"Error: {e}")
