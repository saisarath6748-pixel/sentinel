-- =============================================================
-- Abuse-Ring Sentinel — Supabase Schema + Row Level Security
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- =============================================================

-- merchants table mirrors Supabase Auth users; auth.users.id becomes merchant_id
create table merchants (
    id uuid primary key references auth.users(id),
    name text,
    email text unique,
    avatar_url text
);

create table accounts (
    account_id text primary key,
    merchant_id uuid references merchants(id),
    email text, phone text,
    device_hash text, address_hash text, card_hash text,
    signup_time timestamptz
);

create table orders (
    order_id text primary key,
    account_id text references accounts(account_id),
    merchant_id uuid references merchants(id),
    amount numeric, promo_code_used text, refund_requested boolean,
    order_time timestamptz
);

create table flagged_clusters (
    cluster_id text primary key,
    merchant_id uuid references merchants(id),
    account_ids jsonb,
    suspicion_score numeric,
    status text default 'pending',   -- pending | reviewed | dismissed
    explanation text                 -- filled in on-demand by the LLM layer
);

create table scan_findings (
    id bigint generated always as identity primary key,
    merchant_id uuid references merchants(id),
    file_path text, line_number integer,
    confidence numeric, suggested_fix text,
    scanned_at timestamptz default now()
);

-- =============================================================
-- Row Level Security: enable + restrict each table to its owner
-- =============================================================
alter table accounts enable row level security;
alter table orders enable row level security;
alter table flagged_clusters enable row level security;
alter table scan_findings enable row level security;

create policy "merchant reads own accounts" on accounts
    for select using (auth.uid() = merchant_id);
create policy "merchant reads own orders" on orders
    for select using (auth.uid() = merchant_id);
create policy "merchant reads own clusters" on flagged_clusters
    for select using (auth.uid() = merchant_id);
create policy "merchant updates own clusters" on flagged_clusters
    for update using (auth.uid() = merchant_id);
create policy "merchant reads own scan findings" on scan_findings
    for select using (auth.uid() = merchant_id);
