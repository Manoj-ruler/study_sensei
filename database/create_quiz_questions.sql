create table if not exists quiz_questions (
  id uuid default gen_random_uuid() primary key,
  quiz_id uuid references quizzes(id),
  skill_id uuid references skills(id),
  question text not null,
  options jsonb not null,
  correct_answer int not null,
  user_answer int,
  is_correct boolean,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table quiz_questions enable row level security;

-- Policy to allow all operations
create policy "Enable all access for all users"
on quiz_questions
for all
using (true)
with check (true);
