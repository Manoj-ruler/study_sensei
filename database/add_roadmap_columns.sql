-- Add roadmap column to skills table
ALTER TABLE skills ADD COLUMN IF NOT EXISTS roadmap TEXT;

-- Add roadmap_svg column to store SVG diagram
ALTER TABLE skills ADD COLUMN IF NOT EXISTS roadmap_svg TEXT;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_skills_roadmap ON skills(id) WHERE roadmap IS NOT NULL;
