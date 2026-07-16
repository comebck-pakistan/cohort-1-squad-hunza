-- Enable pgvector extension if you haven't already
create extension if not exists vector;

-- Users (Table 1)
create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  full_name text,
  created_at timestamptz default now()
);

-- Gmail Connection (Table 2)
create table gmail_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  gmail_address text not null,
  refresh_token text not null,
  is_active boolean default true,
  connected_at timestamptz default now()
);

-- Job Posting (Table 3)
create table job_postings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  role_title text not null,
  posting_text text not null,
  embedding vector(384),
  created_at timestamptz default now()
);

-- Emails (Table 4)
create table emails (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  gmail_message_id text unique not null,
  gmail_thread_id text,
  sender_email text,
  sender_name text,
  subject text,
  body_text text,
  received_at timestamptz,
  has_attachment boolean default false,
  is_processed boolean default false,
  created_at timestamptz default now()
);

-- Email Categories (Table 5)
create table email_categories (
  id uuid primary key default gen_random_uuid(),
  email_id uuid references emails(id) on delete cascade,
  category text not null,
  confidence_score float,
  is_duplicate_question boolean default false,
  matched_job_posting_id uuid references job_postings(id),
  classified_at timestamptz default now()
);

-- Email Drafts (Table 6)
create table email_drafts (
  id uuid primary key default gen_random_uuid(),
  email_id uuid references emails(id) on delete cascade,
  draft_body text not null,
  status text default 'pending',
  gmail_draft_id text,
  generated_at timestamptz default now(),
  approved_at timestamptz,
  sent_at timestamptz
);

-- Draft Corrections (Table 7)
create table draft_corrections (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid references email_drafts(id) on delete cascade,
  original_text text,
  corrected_text text,
  corrected_at timestamptz default now()
);

-- Label Corrections (Table 8)
create table label_corrections (
  id uuid primary key default gen_random_uuid(),
  email_id uuid references emails(id) on delete cascade,
  original_category text,
  corrected_category text,
  corrected_at timestamptz default now()
);

-- Candidates (Table 9)
create table candidates (
  id uuid primary key default gen_random_uuid(),
  email_id uuid references emails(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  full_name text,
  candidate_email text,
  role_applied_for text,
  skills_extracted jsonb,
  resume_file_url text,
  created_at timestamptz default now()
);

-- Email Embeddings (Table 10)
create table email_embeddings (
  id uuid primary key default gen_random_uuid(),
  email_id uuid references emails(id) on delete cascade,
  embedding vector(384),
  created_at timestamptz default now()
);