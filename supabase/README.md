# Recova MCP lab Supabase schema

Todo 3 creates the database/storage contract for the Recova debt-brain MCP lab
under the `dev@slit.company` Supabase account. Do not commit real project refs,
service-role keys, bearer tokens, or raw legal evidence.

## Local verification

```sh
supabase db reset --local --no-seed
supabase db diff --local --schema public
psql "$LOCAL_SUPABASE_DB_URL" -f .omo/evidence/recova-mcp-deployment/task-3-smoke.sql
```

`supabase db reset --local --no-seed` reapplies the migrations under
`supabase/migrations/`. `supabase db diff --local --schema public` should produce
no schema drift after the reset.

## Redaction model

- Tables store redacted JSON, source refs, judgment labels, hashes, and storage
  object pointers only.
- Raw OCR text and raw payload columns are intentionally absent.
- `recova_lab_has_blocked_pii()` and table constraints reject obvious
  resident-id, phone, bearer-token, service-key, and Cloudflare-token patterns.
- Raw legal evidence can be represented only as SHA-256 hashes or as objects in
  the private `recova-lab-redacted-evidence` bucket.

## RLS and service-role boundary

All lab tables have row-level security enabled. `service_role` may manage rows
for deployment and trace ingestion. `authenticated` can select/insert/update
only rows whose `lab_owner_email` matches the JWT email claim. The first lab
owner is `dev@slit.company`.

Expose user-facing reads through:

- `public.recova_lab_case_packets_redacted`
- `public.recova_lab_tool_traces_redacted`

Those views are `security_invoker` views, so table RLS still applies.

## Storage policy notes

The private bucket is `recova-lab-redacted-evidence`. The migration gives
`service_role` full bucket-object access, but blocks object names containing raw
or PII path segments and the same obvious secret/PII patterns. Authenticated
client uploads are intentionally not enabled in Todo 3; add them only after a
separate token-bridge task defines path ownership and MIME constraints.
