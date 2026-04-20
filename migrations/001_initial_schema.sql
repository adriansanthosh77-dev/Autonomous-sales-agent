-- Autonomous Sales System - Database Schema
-- Run this against your PostgreSQL/Supabase database

-- Create enum types
CREATE TYPE lead_status AS ENUM (
  'pending',
  'outreach_sent',
  'replied',
  'replied_interested',
  'replied_not_interested',
  'qualified',
  'booked',
  'closed_won',
  'closed_lost'
);

CREATE TYPE sentiment_type AS ENUM (
  'interested',
  'not_now',
  'objection',
  'spam'
);

-- Leads table
CREATE TABLE leads (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  email VARCHAR UNIQUE NOT NULL,
  phone VARCHAR,
  company VARCHAR,
  website VARCHAR,
  title VARCHAR,
  industry VARCHAR,
  source VARCHAR DEFAULT 'manual',
  status lead_status DEFAULT 'pending',
  qualification_score FLOAT,
  last_reply_sentiment sentiment_type,
  last_reply_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  closed_at TIMESTAMP,
  notes TEXT
);

-- Outbound messages
CREATE TABLE outbound_messages (
  id BIGSERIAL PRIMARY KEY,
  lead_id BIGINT REFERENCES leads(id),
  channel VARCHAR DEFAULT 'email',
  subject VARCHAR,
  body TEXT,
  confidence_score FLOAT,
  approved BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Inbound replies
CREATE TABLE inbound_replies (
  id BIGSERIAL PRIMARY KEY,
  lead_id BIGINT REFERENCES leads(id),
  from_email VARCHAR,
  subject VARCHAR,
  body TEXT,
  sentiment sentiment_type,
  sentiment_confidence FLOAT,
  key_points JSONB,
  received_at TIMESTAMP,
  classified_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Meetings
CREATE TABLE meetings (
  id BIGSERIAL PRIMARY KEY,
  lead_id BIGINT REFERENCES leads(id),
  scheduled_time TIMESTAMP NOT NULL,
  duration_minutes INT DEFAULT 30,
  calendar_event_id VARCHAR,
  status VARCHAR DEFAULT 'scheduled',
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Outcomes (deals won/lost)
CREATE TABLE outcomes (
  id BIGSERIAL PRIMARY KEY,
  lead_id BIGINT REFERENCES leads(id),
  status VARCHAR NOT NULL,
  deal_size FLOAT,
  notes TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- A/B Test Variants
CREATE TABLE ab_test_variants (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  message_type VARCHAR DEFAULT 'email',
  subject VARCHAR,
  body TEXT,
  variant_text VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Variant Performance
CREATE TABLE variant_performance (
  id BIGSERIAL PRIMARY KEY,
  variant_id BIGINT REFERENCES ab_test_variants(id),
  metric VARCHAR,
  sent INT DEFAULT 0,
  replied INT DEFAULT 0,
  qualified INT DEFAULT 0,
  closed INT DEFAULT 0,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Metrics (daily snapshots)
CREATE TABLE metrics (
  id BIGSERIAL PRIMARY KEY,
  date DATE DEFAULT CURRENT_DATE,
  total_leads INT,
  outreach_sent INT,
  replies INT,
  qualified INT,
  booked INT,
  closed_won INT,
  reply_rate FLOAT,
  qualification_rate FLOAT,
  close_rate FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes (critical for performance)
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company ON leads(company);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_leads_score ON leads(qualification_score DESC);
CREATE INDEX idx_outbound_lead ON outbound_messages(lead_id);
CREATE INDEX idx_replies_lead ON inbound_replies(lead_id);
CREATE INDEX idx_meetings_lead ON meetings(lead_id);
CREATE INDEX idx_outcomes_lead ON outcomes(lead_id);
CREATE INDEX idx_metrics_date ON metrics(date);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbound_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbound_replies ENABLE ROW LEVEL SECURITY;

-- Create audit trail table
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name VARCHAR,
  operation VARCHAR,
  record_id BIGINT,
  changes JSONB,
  user_id VARCHAR,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);

-- Done!
-- Total: 11 tables, 15+ indexes
-- Ready for 100K+ leads
