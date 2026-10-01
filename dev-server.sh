#!/bin/bash
# Date Versioning - local dev server: builds the site, then serves _site/
# Usage: ./dev-server.sh [port] [--no-dev-mode]
#   port            default: 8080
#   --no-dev-mode   don't force DEV_MODE on for this run (see scripts/dev-server.py)
# Needs Python 3 and `pip install -r requirements.txt`.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=python3
if ! "$PY" -c "import sys" >/dev/null 2>&1; then PY=python; fi
exec "$PY" "$DIR/scripts/dev-server.py" "$@"
