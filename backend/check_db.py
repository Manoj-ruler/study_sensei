import asyncio
from database import supabase

async def check_supabase():
    print("Checking Supabase connection...")
    
    # 1. Check Bucket
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if "documents" in bucket_names:
            print("✅ Bucket 'documents' exists.")
        else:
            print("❌ Bucket 'documents' MISSING. Attempting to create...")
            try:
                supabase.storage.create_bucket("documents", options={"public": True})
                print("✅ Bucket 'documents' created successfully.")
            except Exception as e:
                print(f"❌ Failed to create bucket: {e}")
                print("⚠️ Please create a public bucket named 'documents' in your Supabase dashboard.")
    except Exception as e:
        print(f"❌ Error checking buckets: {e}")

    # 2. Check Tables
    try:
        # Try to select from documents table (limit 1)
        supabase.table("documents").select("*").limit(1).execute()
        print("✅ Table 'documents' exists.")
    except Exception as e:
        print(f"❌ Table 'documents' error: {e}")

    try:
        # Try to select from document_chunks table
        supabase.table("document_chunks").select("*").limit(1).execute()
        print("✅ Table 'document_chunks' exists.")
    except Exception as e:
        print(f"❌ Table 'document_chunks' error: {e}")

if __name__ == "__main__":
    asyncio.run(check_supabase())
