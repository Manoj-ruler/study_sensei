-- Enable RLS on quizzes table
alter table quizzes enable row level security;

-- Policy to allow all operations for now
create policy "Enable all access for all users"
on quizzes
for all
using (true)
with check (true);
