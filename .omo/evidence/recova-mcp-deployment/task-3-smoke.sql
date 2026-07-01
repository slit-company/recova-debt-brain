select 'task-3 smoke: insert redacted Recova lab memory rows' as smoke_step;

insert into public.agent_clients (
  id,
  lab_owner_email,
  client_code,
  client_kind,
  display_name,
  token_hash_sha256,
  metadata
)
values (
  '00000000-0000-4000-8000-000000000301',
  'dev@slit.company',
  'task-3-smoke-client',
  'generic_mcp',
  'Task 3 smoke client',
  encode(extensions.digest('synthetic lab bearer token placeholder', 'sha256'), 'hex'),
  '{"purpose":"todo-3-smoke","raw_text_included":false}'::jsonb
)
on conflict (client_code) do update
set updated_at = now()
returning id;

insert into public.ontology_versions (
  id,
  lab_owner_email,
  ontology_ref,
  version_label,
  source_sha256,
  notes_redacted
)
values (
  '00000000-0000-4000-8000-000000000302',
  'dev@slit.company',
  'recova-debt-ontology-smoke',
  'smoke-v0',
  encode(extensions.digest('recova ontology smoke fixture', 'sha256'), 'hex'),
  'Synthetic smoke ontology version.'
)
on conflict (ontology_ref) do update
set updated_at = now()
returning id;

insert into public.rule_versions (
  id,
  lab_owner_email,
  rule_ref,
  version_label,
  source_sha256,
  notes_redacted
)
values (
  '00000000-0000-4000-8000-000000000303',
  'dev@slit.company',
  'recova-stopgate-rules-smoke',
  'smoke-v0',
  encode(extensions.digest('recova stopgate rules smoke fixture', 'sha256'), 'hex'),
  'Synthetic smoke rule version.'
)
on conflict (rule_ref) do update
set updated_at = now()
returning id;

insert into public.case_packets (
  id,
  lab_owner_email,
  packet_ref,
  client_id,
  ontology_version_id,
  rule_version_id,
  synthetic_label,
  status,
  redacted_case_facts,
  source_refs,
  raw_evidence_sha256
)
values (
  '00000000-0000-4000-8000-000000000304',
  'dev@slit.company',
  'task-3-smoke-case',
  '00000000-0000-4000-8000-000000000301',
  '00000000-0000-4000-8000-000000000302',
  '00000000-0000-4000-8000-000000000303',
  'Synthetic redacted smoke case',
  'evaluated',
  '{"debtor":"[PERSON_REDACTED]","amount_status":"present","raw_text_included":false}'::jsonb,
  '[{"source_ref":"fixture:task-3-smoke","line_start":1,"line_end":1,"confidence":0.91}]'::jsonb,
  array[encode(extensions.digest('synthetic raw evidence omitted', 'sha256'), 'hex')]
)
on conflict (packet_ref) do update
set updated_at = now()
returning id;

insert into public.documents (
  id,
  lab_owner_email,
  case_packet_id,
  document_ref,
  document_type,
  source_ref,
  storage_object_path,
  redacted_summary,
  raw_text_sha256,
  metadata
)
values (
  '00000000-0000-4000-8000-000000000305',
  'dev@slit.company',
  '00000000-0000-4000-8000-000000000304',
  'task-3-smoke-doc',
  'judgment_payment_order',
  'fixture:task-3-smoke',
  'dev/slit/company/smoke/redacted-document.json',
  'Synthetic redacted document summary with no direct identifiers.',
  encode(extensions.digest('synthetic source text omitted', 'sha256'), 'hex'),
  '{"raw_text_included":false,"source_text_included":false}'::jsonb
)
on conflict (document_ref) do update
set updated_at = now()
returning id;

insert into public.evaluation_runs (
  id,
  lab_owner_email,
  run_ref,
  client_id,
  ontology_version_id,
  rule_version_id,
  fixture_manifest_sha256,
  tool_count,
  summary_redacted
)
values (
  '00000000-0000-4000-8000-000000000306',
  'dev@slit.company',
  'task-3-smoke-evaluation',
  '00000000-0000-4000-8000-000000000301',
  '00000000-0000-4000-8000-000000000302',
  '00000000-0000-4000-8000-000000000303',
  encode(extensions.digest('task-3 synthetic fixture manifest', 'sha256'), 'hex'),
  16,
  '{"status":"ok","raw_text_included":false,"tool_count":16}'::jsonb
)
on conflict (run_ref) do update
set updated_at = now()
returning id;

insert into public.expected_answers (
  id,
  lab_owner_email,
  case_packet_id,
  document_id,
  fixture_ref,
  tool_name,
  expected_decision,
  expected_answer_redacted,
  source_refs
)
values (
  '00000000-0000-4000-8000-000000000307',
  'dev@slit.company',
  '00000000-0000-4000-8000-000000000304',
  '00000000-0000-4000-8000-000000000305',
  'fixture:task-3-smoke',
  'check_case_stop_gates',
  '보류',
  '{"decision":"보류","failure_labels":["missing_review"],"raw_text_included":false}'::jsonb,
  '[{"source_ref":"fixture:task-3-smoke","line_start":1,"line_end":1,"confidence":0.91}]'::jsonb
)
returning id;

insert into public.judgment_runs (
  id,
  lab_owner_email,
  evaluation_run_id,
  case_packet_id,
  expected_answer_id,
  tool_name,
  decision,
  confidence,
  failure_labels,
  actual_answer_redacted,
  source_refs,
  correction_status
)
values (
  '00000000-0000-4000-8000-000000000308',
  'dev@slit.company',
  '00000000-0000-4000-8000-000000000306',
  '00000000-0000-4000-8000-000000000304',
  '00000000-0000-4000-8000-000000000307',
  'check_case_stop_gates',
  '보류',
  0.870,
  array['missing_review'],
  '{"decision":"보류","confidence":0.87,"raw_text_included":false}'::jsonb,
  '[{"source_ref":"fixture:task-3-smoke","line_start":1,"line_end":1,"confidence":0.91}]'::jsonb,
  'pending'
)
returning id;

insert into public.tool_traces (
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
  latency_ms
)
values (
  '00000000-0000-4000-8000-000000000309',
  'dev@slit.company',
  '00000000-0000-4000-8000-000000000306',
  '00000000-0000-4000-8000-000000000308',
  '00000000-0000-4000-8000-000000000304',
  '00000000-0000-4000-8000-000000000301',
  'check_case_stop_gates',
  'stopgate',
  'stopgate:check',
  'ok',
  encode(extensions.digest('{"case_packet":"task-3-smoke-case"}', 'sha256'), 'hex'),
  encode(extensions.digest('{"schema_version":"trustgraph-legal-mcp/v1"}', 'sha256'), 'hex'),
  '{"case_packet_ref":"task-3-smoke-case","raw_text_included":false}'::jsonb,
  '{"schema_version":"trustgraph-legal-mcp/v1","decision":"보류","raw_text_included":false}'::jsonb,
  '[{"source_ref":"fixture:task-3-smoke","line_start":1,"line_end":1,"confidence":0.91}]'::jsonb,
  array['synthetic_smoke'],
  12
)
returning id;

insert into public.human_corrections (
  id,
  lab_owner_email,
  tool_trace_id,
  judgment_run_id,
  correction_status,
  reviewer_hash_sha256,
  correction_redacted,
  reason_labels
)
values (
  '00000000-0000-4000-8000-000000000310',
  'dev@slit.company',
  '00000000-0000-4000-8000-000000000309',
  '00000000-0000-4000-8000-000000000308',
  'pending',
  encode(extensions.digest('synthetic reviewer', 'sha256'), 'hex'),
  '{"status":"pending","raw_text_included":false}'::jsonb,
  array['needs_human_review']
)
returning id;

insert into public.document_embeddings (
  id,
  lab_owner_email,
  document_id,
  case_packet_id,
  chunk_ref,
  embedding_model,
  redacted_chunk_summary,
  metadata
)
values (
  '00000000-0000-4000-8000-000000000311',
  'dev@slit.company',
  '00000000-0000-4000-8000-000000000305',
  '00000000-0000-4000-8000-000000000304',
  'line-1',
  'text-embedding-3-small',
  'Synthetic redacted embedding chunk.',
  '{"embedding_pending":true,"raw_text_included":false}'::jsonb
)
on conflict (document_id, chunk_ref, embedding_model) do update
set updated_at = now()
returning id;

select 'task-3 smoke: verify redacted view and RLS owner visibility' as smoke_step;

begin;
set local role authenticated;
set local "request.jwt.claims" = '{"role":"authenticated","email":"outsider@example.com"}';
do $$
declare
  visible_count integer;
begin
  select count(*) into visible_count
  from public.recova_lab_tool_traces_redacted;

  if visible_count <> 0 then
    raise exception 'RLS failure: outsider saw % trace rows', visible_count;
  end if;
end $$;
commit;

begin;
set local role authenticated;
set local "request.jwt.claims" = '{"role":"authenticated","email":"dev@slit.company"}';
do $$
declare
  visible_count integer;
begin
  select count(*) into visible_count
  from public.recova_lab_tool_traces_redacted;

  if visible_count < 1 then
    raise exception 'RLS failure: lab owner saw no trace rows';
  end if;
end $$;
commit;

select 'task-3 smoke: verify synthetic raw PII marker is rejected' as smoke_step;

do $$
begin
  insert into public.documents (
    lab_owner_email,
    case_packet_id,
    document_ref,
    document_type,
    source_ref,
    redacted_summary
  )
  values (
    'dev@slit.company',
    '00000000-0000-4000-8000-000000000304',
    'task-3-smoke-raw-pii-reject',
    'identity_evidence',
    'fixture:task-3-smoke',
    'Synthetic failure marker containing resident_id and 010-0000-0000.'
  );

  raise exception 'raw PII marker was not rejected';
exception
  when check_violation then
    raise notice 'PASS: synthetic raw PII marker rejected by check constraint';
end $$;

select
  (select count(*) from public.case_packets) as case_packets,
  (select count(*) from public.documents) as documents,
  (select count(*) from public.tool_traces) as tool_traces,
  (select count(*) from public.judgment_runs) as judgment_runs,
  (select count(*) from public.document_embeddings) as document_embeddings;

select 'task-3 smoke: PASS' as smoke_step;
