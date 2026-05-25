-- Image Studio: image generation sessions and prompt template library
-- Migration: add-image-studio.sql

-- Image generation sessions
CREATE TABLE IF NOT EXISTS image_sessions (
  id TEXT PRIMARY KEY,  -- UUID string from FastAPI
  article_title TEXT NOT NULL,
  status TEXT DEFAULT 'draft',  -- draft|generating|reviewing|complete
  is_selling_article BOOLEAN DEFAULT FALSE,
  manifest JSONB,
  section_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt template library
CREATE TABLE IF NOT EXISTS prompt_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_type TEXT NOT NULL,
  source TEXT NOT NULL,  -- gemini|pexels
  prompt TEXT NOT NULL,
  rating_sum INTEGER DEFAULT 0,
  rating_count INTEGER DEFAULT 0,
  times_used INTEGER DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_image_sessions_created ON image_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_type ON prompt_templates(section_type, source);
