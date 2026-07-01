begin;

create extension if not exists pgcrypto with schema extensions;
create extension if not exists vector with schema extensions;

do $$
begin
  create type public.recova_lab_client_kind as enum (
    'hermes',
    'claude',
    'openai',
    'generic_mcp',
    'internal'
  );
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.recova_lab_decision as enum (
    '가능',
    '보류',
    '불가능'
  );
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.recova_lab_correction_status as enum (
    'pending',
    'accepted',
    'rejected',
    'applied'
  );
exception
  when duplicate_object then null;
end $$;

do $$
begin
  create type public.recova_lab_pii_profile as enum (
    'redacted',
    'hash_only',
    'synthetic'
  );
exception
  when duplicate_object then null;
end $$;

create or replace function public.recova_lab_has_blocked_pii(value text)
returns boolean
language sql
immutable
parallel safe
returns null on null input
as $$
  select value ~* '([0-9]{6}-[0-9]{7}|[0-9]{3}[-. ][0-9]{3,4}[-. ][0-9]{4}|resident[_ -]?id|national[_ -]?id|rrn|authorization:[[:space:]]*bearer|service_role|supabase_service_role_key|cloudflare_api_token)';
$$;

create or replace function public.recova_lab_jsonb_has_blocked_pii(value jsonb)
returns boolean
language sql
immutable
parallel safe
returns null on null input
as $$
  select public.recova_lab_has_blocked_pii(value::text);
$$;

create or replace function public.recova_lab_sha256_array_is_valid(value text[])
returns boolean
language sql
immutable
parallel safe
returns null on null input
as $$
  select coalesce(bool_and(hash_value ~ '^[0-9a-f]{64}$'), true)
  from unnest(value) as hash_value;
$$;

create or replace function public.recova_lab_current_email()
returns text
language sql
stable
as $$
  select nullif(coalesce(auth.jwt() ->> 'email', ''), '');
$$;

create or replace function public.recova_lab_is_service_role()
returns boolean
language sql
stable
as $$
  select current_user = 'service_role'
    or coalesce(auth.jwt() ->> 'role', '') = 'service_role';
$$;

create or replace function public.recova_lab_can_access(owner_email text)
returns boolean
language sql
stable
returns null on null input
as $$
  select public.recova_lab_is_service_role()
    or owner_email = public.recova_lab_current_email();
$$;

create or replace function public.recova_lab_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.agent_clients (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  client_code text not null unique,
  client_kind public.recova_lab_client_kind not null,
  display_name text not null,
  token_hash_sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  last_seen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint agent_clients_owner_email_lower check (lab_owner_email = lower(lab_owner_email)),
  constraint agent_clients_token_hash_sha256_format check (
    token_hash_sha256 is null or token_hash_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint agent_clients_metadata_redacted check (
    not public.recova_lab_jsonb_has_blocked_pii(metadata)
  ),
  constraint agent_clients_text_redacted check (
    not public.recova_lab_has_blocked_pii(display_name)
    and not public.recova_lab_has_blocked_pii(client_code)
  )
);

create table public.ontology_versions (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  ontology_ref text not null unique,
  version_label text not null,
  source_sha256 text not null,
  notes_redacted text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ontology_versions_source_sha256_format check (source_sha256 ~ '^[0-9a-f]{64}$'),
  constraint ontology_versions_notes_redacted check (
    notes_redacted is null or not public.recova_lab_has_blocked_pii(notes_redacted)
  )
);

create table public.rule_versions (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  rule_ref text not null unique,
  version_label text not null,
  source_sha256 text not null,
  notes_redacted text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint rule_versions_source_sha256_format check (source_sha256 ~ '^[0-9a-f]{64}$'),
  constraint rule_versions_notes_redacted check (
    notes_redacted is null or not public.recova_lab_has_blocked_pii(notes_redacted)
  )
);

create table public.case_packets (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  packet_ref text not null unique,
  client_id uuid references public.agent_clients(id) on delete set null,
  ontology_version_id uuid references public.ontology_versions(id) on delete set null,
  rule_version_id uuid references public.rule_versions(id) on delete set null,
  synthetic_label text,
  status text not null default 'queued',
  pii_profile public.recova_lab_pii_profile not null default 'redacted',
  redacted_case_facts jsonb not null default '{}'::jsonb,
  source_refs jsonb not null default '[]'::jsonb,
  raw_evidence_sha256 text[] not null default '{}'::text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint case_packets_status_check check (status in ('queued', 'evaluated', 'corrected', 'archived')),
  constraint case_packets_redacted_case_facts_check check (
    not public.recova_lab_jsonb_has_blocked_pii(redacted_case_facts)
  ),
  constraint case_packets_source_refs_check check (
    not public.recova_lab_jsonb_has_blocked_pii(source_refs)
  ),
  constraint case_packets_hashes_check check (
    public.recova_lab_sha256_array_is_valid(raw_evidence_sha256)
  )
);

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  case_packet_id uuid not null references public.case_packets(id) on delete cascade,
  document_ref text not null unique,
  document_type text not null,
  source_ref text not null,
  storage_bucket text not null default 'recova-lab-redacted-evidence',
  storage_object_path text,
  pii_profile public.recova_lab_pii_profile not null default 'redacted',
  redacted_summary text,
  raw_text_sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint documents_raw_text_sha256_format check (
    raw_text_sha256 is null or raw_text_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint documents_redacted_summary_check check (
    redacted_summary is null or not public.recova_lab_has_blocked_pii(redacted_summary)
  ),
  constraint documents_metadata_check check (
    not public.recova_lab_jsonb_has_blocked_pii(metadata)
  ),
  constraint documents_storage_path_check check (
    storage_object_path is null
    or (
      storage_object_path !~* '(^|/)raw(/|$)'
      and storage_object_path !~* '(^|/)pii(/|$)'
      and not public.recova_lab_has_blocked_pii(storage_object_path)
    )
  )
);

create table public.evaluation_runs (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  run_ref text not null unique,
  client_id uuid references public.agent_clients(id) on delete set null,
  ontology_version_id uuid references public.ontology_versions(id) on delete set null,
  rule_version_id uuid references public.rule_versions(id) on delete set null,
  fixture_manifest_sha256 text,
  tool_count integer,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  summary_redacted jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint evaluation_runs_fixture_manifest_sha256_format check (
    fixture_manifest_sha256 is null or fixture_manifest_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint evaluation_runs_tool_count_check check (tool_count is null or tool_count >= 0),
  constraint evaluation_runs_summary_redacted_check check (
    not public.recova_lab_jsonb_has_blocked_pii(summary_redacted)
  )
);

create table public.expected_answers (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  case_packet_id uuid references public.case_packets(id) on delete cascade,
  document_id uuid references public.documents(id) on delete set null,
  fixture_ref text not null,
  tool_name text not null,
  expected_decision public.recova_lab_decision,
  expected_answer_redacted jsonb not null default '{}'::jsonb,
  source_refs jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint expected_answers_expected_answer_redacted_check check (
    not public.recova_lab_jsonb_has_blocked_pii(expected_answer_redacted)
  ),
  constraint expected_answers_source_refs_check check (
    not public.recova_lab_jsonb_has_blocked_pii(source_refs)
  )
);

create table public.judgment_runs (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  evaluation_run_id uuid references public.evaluation_runs(id) on delete cascade,
  case_packet_id uuid references public.case_packets(id) on delete cascade,
  expected_answer_id uuid references public.expected_answers(id) on delete set null,
  tool_name text not null,
  decision public.recova_lab_decision not null,
  confidence numeric(4, 3) not null,
  failure_labels text[] not null default '{}'::text[],
  actual_answer_redacted jsonb not null default '{}'::jsonb,
  source_refs jsonb not null default '[]'::jsonb,
  correction_status public.recova_lab_correction_status not null default 'pending',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint judgment_runs_confidence_check check (confidence >= 0 and confidence <= 1),
  constraint judgment_runs_actual_answer_redacted_check check (
    not public.recova_lab_jsonb_has_blocked_pii(actual_answer_redacted)
  ),
  constraint judgment_runs_source_refs_check check (
    not public.recova_lab_jsonb_has_blocked_pii(source_refs)
  )
);

create table public.tool_traces (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  evaluation_run_id uuid references public.evaluation_runs(id) on delete cascade,
  judgment_run_id uuid references public.judgment_runs(id) on delete cascade,
  case_packet_id uuid references public.case_packets(id) on delete cascade,
  client_id uuid references public.agent_clients(id) on delete set null,
  tool_name text not null,
  group_name text not null,
  scope text not null,
  status text not null default 'ok',
  arguments_hash_sha256 text not null,
  envelope_hash_sha256 text not null,
  redacted_arguments jsonb not null default '{}'::jsonb,
  redacted_result jsonb not null default '{}'::jsonb,
  source_refs jsonb not null default '[]'::jsonb,
  warnings text[] not null default '{}'::text[],
  latency_ms integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tool_traces_status_check check (status in ('ok', 'rejected', 'unknown_tool', 'error')),
  constraint tool_traces_hashes_check check (
    arguments_hash_sha256 ~ '^[0-9a-f]{64}$'
    and envelope_hash_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint tool_traces_redacted_arguments_check check (
    not public.recova_lab_jsonb_has_blocked_pii(redacted_arguments)
  ),
  constraint tool_traces_redacted_result_check check (
    not public.recova_lab_jsonb_has_blocked_pii(redacted_result)
  ),
  constraint tool_traces_source_refs_check check (
    not public.recova_lab_jsonb_has_blocked_pii(source_refs)
  ),
  constraint tool_traces_latency_check check (latency_ms is null or latency_ms >= 0)
);

create table public.human_corrections (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  tool_trace_id uuid references public.tool_traces(id) on delete cascade,
  judgment_run_id uuid references public.judgment_runs(id) on delete cascade,
  correction_status public.recova_lab_correction_status not null default 'pending',
  reviewer_hash_sha256 text,
  correction_redacted jsonb not null default '{}'::jsonb,
  reason_labels text[] not null default '{}'::text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint human_corrections_reviewer_hash_sha256_format check (
    reviewer_hash_sha256 is null or reviewer_hash_sha256 ~ '^[0-9a-f]{64}$'
  ),
  constraint human_corrections_correction_redacted_check check (
    not public.recova_lab_jsonb_has_blocked_pii(correction_redacted)
  )
);

create table public.document_embeddings (
  id uuid primary key default gen_random_uuid(),
  lab_owner_email text not null default 'dev@slit.company',
  document_id uuid not null references public.documents(id) on delete cascade,
  case_packet_id uuid references public.case_packets(id) on delete cascade,
  chunk_ref text not null,
  embedding_model text not null,
  embedding extensions.vector(1536),
  redacted_chunk_summary text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint document_embeddings_unique_chunk unique (document_id, chunk_ref, embedding_model),
  constraint document_embeddings_redacted_chunk_summary_check check (
    redacted_chunk_summary is null or not public.recova_lab_has_blocked_pii(redacted_chunk_summary)
  ),
  constraint document_embeddings_metadata_check check (
    not public.recova_lab_jsonb_has_blocked_pii(metadata)
  )
);

create index agent_clients_owner_idx on public.agent_clients(lab_owner_email);
create index case_packets_owner_status_idx on public.case_packets(lab_owner_email, status);
create index documents_case_packet_idx on public.documents(case_packet_id);
create index evaluation_runs_owner_started_idx on public.evaluation_runs(lab_owner_email, started_at desc);
create index expected_answers_case_packet_idx on public.expected_answers(case_packet_id);
create index judgment_runs_eval_idx on public.judgment_runs(evaluation_run_id);
create index tool_traces_eval_tool_idx on public.tool_traces(evaluation_run_id, tool_name);
create index human_corrections_trace_idx on public.human_corrections(tool_trace_id);
create index document_embeddings_document_idx on public.document_embeddings(document_id);

create or replace view public.recova_lab_case_packets_redacted
with (security_invoker = true) as
select
  id,
  lab_owner_email,
  packet_ref,
  client_id,
  synthetic_label,
  status,
  pii_profile,
  redacted_case_facts,
  source_refs,
  created_at,
  updated_at
from public.case_packets;

create or replace view public.recova_lab_tool_traces_redacted
with (security_invoker = true) as
select
  id,
  lab_owner_email,
  evaluation_run_id,
  judgment_run_id,
  case_packet_id,
  client_id,
  tool_name,
  group_name,
  scope,
  status,
  arguments_hash_sha256,
  envelope_hash_sha256,
  redacted_arguments,
  redacted_result,
  source_refs,
  warnings,
  latency_ms,
  created_at
from public.tool_traces;

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'agent_clients',
    'ontology_versions',
    'rule_versions',
    'case_packets',
    'documents',
    'evaluation_runs',
    'expected_answers',
    'judgment_runs',
    'tool_traces',
    'human_corrections',
    'document_embeddings'
  ]
  loop
    execute format('alter table public.%I enable row level security', table_name);

    execute format(
      'create policy %I on public.%I for all to service_role using (true) with check (true)',
      table_name || '_service_role_all',
      table_name
    );

    execute format(
      'create policy %I on public.%I for select to authenticated using (public.recova_lab_can_access(lab_owner_email))',
      table_name || '_authenticated_owner_select',
      table_name
    );

    execute format(
      'create policy %I on public.%I for insert to authenticated with check (public.recova_lab_can_access(lab_owner_email))',
      table_name || '_authenticated_owner_insert',
      table_name
    );

    execute format(
      'create policy %I on public.%I for update to authenticated using (public.recova_lab_can_access(lab_owner_email)) with check (public.recova_lab_can_access(lab_owner_email))',
      table_name || '_authenticated_owner_update',
      table_name
    );
  end loop;
end $$;

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'agent_clients',
    'ontology_versions',
    'rule_versions',
    'case_packets',
    'documents',
    'evaluation_runs',
    'expected_answers',
    'judgment_runs',
    'tool_traces',
    'human_corrections',
    'document_embeddings'
  ]
  loop
    execute format(
      'create trigger %I before update on public.%I for each row execute function public.recova_lab_touch_updated_at()',
      table_name || '_touch_updated_at',
      table_name
    );
  end loop;
end $$;

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'recova-lab-redacted-evidence',
  'recova-lab-redacted-evidence',
  false,
  52428800,
  array[
    'application/json',
    'application/pdf',
    'image/png',
    'image/jpeg',
    'text/markdown',
    'text/plain'
  ]
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists recova_lab_bucket_service_role_all on storage.objects;
create policy recova_lab_bucket_service_role_all
on storage.objects
for all
to service_role
using (bucket_id = 'recova-lab-redacted-evidence')
with check (
  bucket_id = 'recova-lab-redacted-evidence'
  and name !~* '(^|/)raw(/|$)'
  and name !~* '(^|/)pii(/|$)'
  and not public.recova_lab_has_blocked_pii(name)
);

grant usage on schema public to anon, authenticated, service_role;
grant select, insert, update on all tables in schema public to authenticated;
grant select on public.recova_lab_case_packets_redacted to authenticated, service_role;
grant select on public.recova_lab_tool_traces_redacted to authenticated, service_role;
grant all privileges on all tables in schema public to service_role;
grant execute on function public.recova_lab_has_blocked_pii(text) to authenticated, service_role;
grant execute on function public.recova_lab_jsonb_has_blocked_pii(jsonb) to authenticated, service_role;
grant execute on function public.recova_lab_sha256_array_is_valid(text[]) to authenticated, service_role;
grant execute on function public.recova_lab_can_access(text) to authenticated, service_role;

commit;
