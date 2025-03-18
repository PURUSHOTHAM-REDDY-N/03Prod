-- Add priority column to subtopic_confidences table
ALTER TABLE subtopic_confidences ADD COLUMN priority BOOLEAN DEFAULT 0 NOT NULL; 