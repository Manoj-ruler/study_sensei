import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
anon_key = os.environ.get("SUPABASE_KEY")

if service_role_key:
    key = service_role_key
else:
    key = anon_key

if not url or not key:
    raise ValueError("Supabase URL and Key must be set in .env file")

supabase: Client = create_client(url, key)
