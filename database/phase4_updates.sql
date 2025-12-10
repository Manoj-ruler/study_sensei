-- Add is_technical column to skills table
-- Default to true to maintain backward compatibility (existing skills presumably have coding)
ALTER TABLE public.skills ADD COLUMN IF NOT EXISTS is_technical BOOLEAN DEFAULT TRUE;

-- Add mode column to messages table for persisting chat tabs
ALTER TABLE public.messages ADD COLUMN IF NOT EXISTS mode text DEFAULT 'explain';
