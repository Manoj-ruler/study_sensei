-- Enable RLS on documents table
alter table documents enable row level security;

-- Policy to allow all operations for now (since backend uses anon key without user token in this MVP setup)
-- In a real app, you would check auth.uid() = user_id
create policy "Enable all access for all users"
on documents
for all
using (true)
with check (true);

-- Enable RLS on document_chunks table
alter table document_chunks enable row level security;

create policy "Enable all access for all users"
on document_chunks
for all
using (true)
with check (true);

-- Storage Policies
-- Allow public access to 'documents' bucket
create policy "Public Access"
on storage.objects for all
using ( bucket_id = 'documents' )
with check ( bucket_id = 'documents' );
