-- Phase 5: Analytics Schema

-- Progress Metrics Table
CREATE TABLE IF NOT EXISTS public.progress_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    skill_id UUID REFERENCES public.skills(id) ON DELETE CASCADE,
    activity_type TEXT CHECK (activity_type IN ('quiz', 'code', 'chat')),
    score INTEGER, -- For quizzes/code challenges
    max_score INTEGER,
    metadata JSONB, -- Store extra info (e.g., topics covered)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.progress_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own metrics" ON public.progress_metrics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own metrics" ON public.progress_metrics FOR INSERT WITH CHECK (auth.uid() = user_id);
