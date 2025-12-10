-- Enable RLS on chats table
alter table chats enable row level security;

create policy "Enable all access for all users"
on chats
for all
using (true)
with check (true);

-- Enable RLS on messages table
alter table messages enable row level security;

create policy "Enable all access for all users"
on messages
for all
using (true)
with check (true);
