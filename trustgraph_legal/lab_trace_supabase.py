from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from trustgraph_legal.lab_trace import (
    JsonAnyObject,
    JsonRows,
    SupabaseConfig,
    TraceInvocation,
    evaluation_run_row,
    judgment_run_row,
    linked_tool_trace_row,
)


@dataclass(frozen=True)
class JudgmentTraceRequest:
    invocation: TraceInvocation
    config: SupabaseConfig
    run_ref: str
    tool_count: Optional[int] = None


def write_judgment_trace_to_supabase(request: JudgmentTraceRequest) -> JsonAnyObject:
    evaluation_rows = post_supabase_rows(
        "evaluation_runs",
        [evaluation_run_row(request.invocation, request.run_ref, request.tool_count)],
        request.config,
    )
    evaluation_id = _inserted_id(evaluation_rows, "evaluation_runs")
    judgment_rows = post_supabase_rows(
        "judgment_runs",
        [judgment_run_row(request.invocation, evaluation_id)],
        request.config,
    )
    judgment_id = _inserted_id(judgment_rows, "judgment_runs")
    trace_rows = post_supabase_rows(
        "tool_traces",
        [linked_tool_trace_row(request.invocation, evaluation_id, judgment_id)],
        request.config,
    )
    return {
        "status": "recorded",
        "evaluation_status": "recorded",
        "judgment_status": "recorded",
        "tool_trace_status": "recorded",
        "evaluation_run_id": evaluation_id,
        "judgment_run_id": judgment_id,
        "tool_trace_row_count": len(trace_rows),
    }


def post_supabase_rows(
    table_name: str,
    rows: JsonRows,
    config: SupabaseConfig,
) -> JsonRows:
    endpoint = "{}/rest/v1/{}".format(config.url.rstrip("/"), table_name)
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(rows, ensure_ascii=False).encode("utf-8"),
        headers={
            "apikey": config.service_role_key,
            "authorization": "Bearer {}".format(config.service_role_key),
            "content-type": "application/json",
            "prefer": "return=representation",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
    inserted: Any = json.loads(body) if body else []
    return inserted if isinstance(inserted, list) else []


def _inserted_id(rows: List[Dict[str, Any]], table_name: str) -> str:
    if not rows:
        raise RuntimeError("{} insert returned no rows".format(table_name))
    row_id = rows[0].get("id")
    if not isinstance(row_id, str) or not row_id:
        raise RuntimeError("{} insert returned no id".format(table_name))
    return row_id
