# Task 2 Rollback-Safe DNS Mutation Notes

Observed: 2026-07-01 22:53:01 KST

No mutation was performed in Todo 2.

## Current DNS State

- `slit.company` authoritative DNS: Cloudflare.
- Authoritative nameservers: `clarissa.ns.cloudflare.com`, `keaton.ns.cloudflare.com`.
- Registrar: GoDaddy.com, LLC.
- `mcp-lab.recova.slit.company`: NXDOMAIN for A, AAAA, CNAME, TXT, and TYPE65 at the time of this audit.

## Future Create Prerequisites

Do not create the record until all are true:

1. The lab server IP is known and recorded as `<SERVER_IP>`.
2. Cloudflare API access is available through a local secret variable or a secure operator session.
3. A fresh pre-change snapshot is saved:

```sh
dig +short NS slit.company
dig +nocmd mcp-lab.recova.slit.company A +noall +answer +authority +comments
dig +nocmd mcp-lab.recova.slit.company CNAME +noall +answer +authority +comments
```

## Future Cloudflare Create Template

Use the official Cloudflare DNS Records API after replacing placeholders. Keep `proxied:false` unless the deployment owner explicitly chooses Cloudflare proxying for the MCP transport.

```sh
curl -sS -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "mcp-lab.recova.slit.company",
    "content": "<SERVER_IP>",
    "ttl": 1,
    "proxied": false,
    "comment": "Recova MCP lab endpoint"
  }' | jq '{success, result: {id, name, type, content, ttl, proxied, comment}}'
```

Save the returned record id as `<RECORD_ID>` in the Todo 9 evidence bundle.

## Rollback Template

Because the current state is NXDOMAIN, rollback for a newly created A record is deletion of that new record:

```sh
curl -sS -X DELETE "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records/<RECORD_ID>" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | jq '{success, result}'
```

Then verify the rollback:

```sh
dig +short mcp-lab.recova.slit.company
dig +nocmd mcp-lab.recova.slit.company A +noall +answer +authority +comments
```

Expected rollback result: no `dig +short` output and an authoritative NXDOMAIN under the `slit.company` Cloudflare SOA.

## GoDaddy Note

GoDaddy is the registrar, not the active DNS authority. Do not create application DNS records through GoDaddy while the domain delegates to Cloudflare. GoDaddy work is only needed if delegation itself must change.
