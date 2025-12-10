from database import supabase

try:
    print("Checking 'quizzes' table...")
    quizzes = supabase.table("quizzes").select("*").limit(1).execute()
    print(f"Quizzes columns: {quizzes.data[0].keys() if quizzes.data else 'Table empty or no access'}")
    
    # If empty, try to insert a dummy to see columns (or check error) if select didn't return keys
    if not quizzes.data:
        print("Table empty. Trying to infer columns from error or just assuming standard schema.")
        # We can try to get schema info if possible, or just proceed with assumptions based on typical setup
        
except Exception as e:
    print(f"Error: {e}")
