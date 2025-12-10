from database import supabase

try:
    # Check if 'chats' table exists and get a sample
    print("Checking 'chats' table...")
    chats = supabase.table("chats").select("*").limit(1).execute()
    print(f"Chats columns: {chats.data[0].keys() if chats.data else 'Table empty or no access'}")

    # Check if 'messages' table exists and get a sample
    print("\nChecking 'messages' table...")
    messages = supabase.table("messages").select("*").limit(1).execute()
    print(f"Messages columns: {messages.data[0].keys() if messages.data else 'Table empty or no access'}")

except Exception as e:
    print(f"Error: {e}")
