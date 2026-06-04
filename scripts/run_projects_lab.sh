#!/usr/bin/env bash
# Projects Lab (all portfolio modules including Materials & Logistics).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
[[ -f .env ]] && set -a && source .env && set +a
echo "Projects Lab → http://localhost:8502"
echo "  Sidebar → Materials & Logistics · set Real-world mode · Run Example 1 & 2"
exec streamlit run app/projects_lab.py --server.port 8502
