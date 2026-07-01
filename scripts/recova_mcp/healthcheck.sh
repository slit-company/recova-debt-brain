#!/usr/bin/env sh
set -eu

python - <<'PY'
import socket

with socket.create_connection(("127.0.0.1", 8000), timeout=3):
    pass
PY
