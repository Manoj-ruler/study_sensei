-- Add status and error_message columns to documents table for async processing
ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS status text DEFAULT 'pending';
ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS error_message text;
