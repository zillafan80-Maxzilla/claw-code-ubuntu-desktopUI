#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CLAW_DESKTOP_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}/claw-code-desktop"

if [[ -f "$ROOT/.env.desktop" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.env.desktop"
fi

export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://127.0.0.1:8001/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-local-dev-token}"
export CLAW_DESKTOP_MODEL="${CLAW_DESKTOP_MODEL:-openai/gemma-4-31b-it-q8-prod}"
export CLAW_TOOL_CALL_STYLE="${CLAW_TOOL_CALL_STYLE:-auto}"

cleanup() {
  python3 "$ROOT/main.py" --cleanup-only >/dev/null 2>&1 || true
}

cleanup
trap cleanup EXIT INT TERM
python3 "$ROOT/main.py"
