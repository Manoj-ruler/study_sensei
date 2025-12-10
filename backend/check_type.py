from database import supabase

try:
    docs = supabase.table("documents").select("skill_id").limit(1).execute()
    if docs.data:
        print(f"skill_id: {docs.data[0]['skill_id']}")
        print(f"Type: {type(docs.data[0]['skill_id'])}")
    else:
        print("No documents found")
except Exception as e:
    print(f"Error: {e}")
