-- Function to match documents using cosine similarity with skill_id filtering
drop function if exists match_documents;

create or replace function match_documents (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  filter_skill_id uuid
)
returns table (
  id uuid,
  content text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    document_chunks.id,
    document_chunks.content,
    1 - (document_chunks.embedding <=> query_embedding) as similarity
  from document_chunks
  join documents on document_chunks.document_id = documents.id
  where 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  and documents.skill_id = filter_skill_id
  order by document_chunks.embedding <=> query_embedding
  limit match_count;
end;
$$;
