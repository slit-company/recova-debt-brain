# C Supabase Schema Report

Member: C `supabase-schema`  
Thread: codex://threads/019f1def-26d4-73b0-bbcc-fdb9d999338e  
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-89938d95/worktrees/C`  
Branch: `team/team-89938d95/C`

## Deliverable

Implemented Todo 3 Supabase lab project artifacts:

- `supabase/config.toml`
- `supabase/README.md`
- `supabase/migrations/20260701000100_recova_lab_memory.sql`
- `.omo/evidence/recova-mcp-deployment/task-3-smoke.sql`

The migration creates:

- `agent_clients`
- `case_packets`
- `documents`
- `tool_traces`
- `judgment_runs`
- `expected_answers`
- `human_corrections`
- `ontology_versions`
- `rule_versions`
- `evaluation_runs`
- `document_embeddings` with `extensions.vector(1536)`
- `recova_lab_case_packets_redacted`
- `recova_lab_tool_traces_redacted`
- private storage bucket `recova-lab-redacted-evidence`

## Security Shape

- No raw OCR/text payload columns were added.
- Sensitive source material is represented by hashes, redacted JSON, source refs, and storage object pointers.
- Check constraints reject obvious raw resident-id, phone, bearer-token, service-key, and Cloudflare-token patterns.
- RLS is enabled on all lab tables.
- `service_role` can manage lab rows and bucket objects.
- `authenticated` can select/insert/update only rows where `lab_owner_email` matches the JWT email claim.
- Storage object mutation is service-role-only in Todo 3; authenticated uploads are intentionally left for a later token-bridge design.

## Verification

Evidence root: `.omo/evidence/recova-mcp-deployment/`

- PASS: `supabase start`
  - Evidence: `task-3-supabase-start.txt`
  - Raw startup output was not retained because Supabase printed local development keys.
- PASS: `supabase db reset --local --no-seed`
  - Evidence: `task-3-db-reset.txt`
- PASS: `supabase db diff --local --schema public`
  - Evidence: `task-3-db-diff.txt`
  - Result: no schema changes found.
- PASS: smoke SQL via containerized psql
  - Invocation: `docker exec -i supabase_db_recova-mcp-lab psql -U postgres -d postgres -v ON_ERROR_STOP=1 < .omo/evidence/recova-mcp-deployment/task-3-smoke.sql`
  - Evidence: `task-3-supabase-smoke.txt`
  - Verified one redacted trace/evaluation path, outsider RLS denial, owner visibility for `dev@slit.company`, and rejection of a synthetic raw PII marker.
- PASS: `supabase db lint --local`
  - Evidence: `task-3-db-lint.txt`
  - Result: no schema errors found.

Host `psql` was not installed, so the smoke used the local Supabase Postgres container as the equivalent DB CLI.

## Notes

- Supabase CLI available: `2.105.0`.
- CLI reported a newer version available, but Todo 3 did not require CLI upgrade.
- No remote Supabase project was linked or mutated.
- No real Supabase secrets were used or committed.
