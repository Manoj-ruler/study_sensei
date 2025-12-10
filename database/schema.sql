-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Create a table for public profiles (linked to Supabase Auth)
create table public.profiles (
  id uuid references auth.users not null primary key,
  full_name text,
  avatar_url text,
  updated_at timestamp with time zone,
  
  constraint username_length check (char_length(full_name) >= 3)
);

-- Enable Row Level Security (RLS)
alter table public.profiles enable row level security;

-- Create policies for profiles
create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

create policy "Users can insert their own profile."
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

-- Skills / Learning Paths Table
create table public.skills (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  title text not null,
  description text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
alter table public.skills enable row level security;
create policy "Users can view own skills" on public.skills for select using (auth.uid() = user_id);
create policy "Users can insert own skills" on public.skills for insert with check (auth.uid() = user_id);
create policy "Users can delete own skills" on public.skills for delete using (auth.uid() = user_id);

-- Documents Table
create table public.documents (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  skill_id uuid references public.skills on delete cascade,
  filename text not null,
  file_url text not null,
  processed boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
alter table public.documents enable row level security;
create policy "Users can view own documents" on public.documents for select using (auth.uid() = user_id);
create policy "Users can insert own documents" on public.documents for insert with check (auth.uid() = user_id);

-- Document Chunks Table (for RAG)
create table public.document_chunks (
  id uuid default gen_random_uuid() primary key,
  document_id uuid references public.documents on delete cascade not null,
  content text not null,
  embedding vector(384), -- Using 384 dimensions for all-MiniLM-L6-v2
  chunk_index integer,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
alter table public.document_chunks enable row level security;
create policy "Users can view own chunks" on public.document_chunks for select 
using (exists (select 1 from public.documents where id = document_chunks.document_id and user_id = auth.uid()));

-- Chats Table
create table public.chats (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  skill_id uuid references public.skills on delete cascade,
  title text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
alter table public.chats enable row level security;
create policy "Users can view own chats" on public.chats for select using (auth.uid() = user_id);
create policy "Users can insert own chats" on public.chats for insert with check (auth.uid() = user_id);

-- Messages Table
create table public.messages (
  id uuid default gen_random_uuid() primary key,
  chat_id uuid references public.chats on delete cascade not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
alter table public.messages enable row level security;
create policy "Users can view own messages" on public.messages for select 
using (exists (select 1 from public.chats where id = messages.chat_id and user_id = auth.uid()));
create policy "Users can insert own messages" on public.messages for insert 
with check (exists (select 1 from public.chats where id = messages.chat_id and user_id = auth.uid()));

-- Quizzes Table
create table public.quizzes (
  id uuid default gen_random_uuid() primary key,
  skill_id uuid references public.skills on delete cascade not null,
  score integer,
  total_questions integer,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
alter table public.quizzes enable row level security;
create policy "Users can view own quizzes" on public.quizzes for select using (exists (select 1 from public.skills where id = quizzes.skill_id and user_id = auth.uid()));

-- Function to handle new user signup (Trigger)
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
