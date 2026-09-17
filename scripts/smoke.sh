#!/usr/bin/env bash
# Smoke: health → register → thread → upload fixture (local embeddings) →
# in-corpus chat → OOD refusal.
# Chat needs a live OPENAI_API_KEY, XAI_API_KEY, or ANTHROPIC_API_KEY.
# No mock mode. Exit 2 if no live chat key (CI should skip).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BASE="${SMOKE_BASE_URL:-http://127.0.0.1:8080}"
FIXTURE="$ROOT/api/tests/fixtures/sample.pdf"
CANNED="I don't have that in your documents."

load_env() {
  if [[ -f "$ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    source "$ROOT/.env"
    set +a
  fi
}

load_env

is_live() {
  local key="${1:-}"
  case "$key" in
    "" | sk-replace-me | sk-not-set | sk-test*) return 1 ;;
    *) return 0 ;;
  esac
}

PROVIDER=""
CHAT_KEY=""
if is_live "${OPENAI_API_KEY:-}"; then
  PROVIDER="openai"
  CHAT_KEY="$OPENAI_API_KEY"
elif is_live "${XAI_API_KEY:-}"; then
  PROVIDER="xai"
  CHAT_KEY="$XAI_API_KEY"
elif is_live "${ANTHROPIC_API_KEY:-}"; then
  PROVIDER="anthropic"
  CHAT_KEY="$ANTHROPIC_API_KEY"
else
  echo "smoke.sh requires a live OPENAI_API_KEY, XAI_API_KEY, or ANTHROPIC_API_KEY. CI without a key should skip this script."
  exit 2
fi

if [[ ! -f "$FIXTURE" ]]; then
  echo "missing fixture: $FIXTURE" >&2
  exit 1
fi

COOKIE="$(mktemp)"
trap 'rm -f "$COOKIE"' EXIT

json_get() {
  python3 -c "import json,sys; print(json.load(sys.stdin)$1)"
}

echo "== health =="
HEALTH="$(curl -fsS "$BASE/api/health")"
echo "$HEALTH" | grep -q '"status":"ok"' || { echo "health failed: $HEALTH" >&2; exit 1; }

EMAIL="smoke-$(date +%s)@example.com"
PASSWORD="correct-horse-battery"

echo "== register $EMAIL =="
REG="$(curl -fsS -c "$COOKIE" -b "$COOKIE" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  "$BASE/api/auth/register")"
echo "$REG" | json_get "['email']" | grep -q "@" || { echo "register failed: $REG" >&2; exit 1; }

echo "== save $PROVIDER chat key =="
FIELD="${PROVIDER}_api_key"
curl -fsS -c "$COOKIE" -b "$COOKIE" -H "Content-Type: application/json" \
  -d "{\"${FIELD}\":$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$CHAT_KEY"),\"chat_provider\":\"$PROVIDER\"}" \
  "$BASE/api/settings/llm" >/dev/null

echo "== create thread =="
THREAD="$(curl -fsS -c "$COOKIE" -b "$COOKIE" -H "Content-Type: application/json" \
  -d '{"title":"smoke"}' \
  "$BASE/api/threads")"
TID="$(echo "$THREAD" | json_get "['id']")"
[[ -n "$TID" ]] || { echo "thread failed: $THREAD" >&2; exit 1; }

echo "== upload sample.pdf (local embeddings) =="
UP="$(curl -fsS -c "$COOKIE" -b "$COOKIE" \
  -F "files=@${FIXTURE};type=application/pdf" \
  "$BASE/api/threads/${TID}/documents")"
STATUS="$(echo "$UP" | json_get "[0]['status']")"
MODEL="$(echo "$UP" | json_get "[0]['embedding_model']")"
[[ "$STATUS" == "ready" ]] || { echo "upload not ready: $UP" >&2; exit 1; }
echo "$MODEL" | grep -q MiniLM || { echo "expected MiniLM embedding_model: $UP" >&2; exit 1; }

echo "== in-corpus query =="
ASK="$(curl -fsS -c "$COOKIE" -b "$COOKIE" -H "Content-Type: application/json" \
  -d '{"content":"what text is in the document?"}' \
  "$BASE/api/threads/${TID}/messages")"
ANS="$(echo "$ASK" | json_get "['assistant_message']['content']")"
if [[ "$ANS" == "$CANNED" ]]; then
  echo "expected in-corpus answer, got canned refusal: $ASK" >&2
  exit 1
fi
N_SRC="$(echo "$ASK" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['assistant_message']['sources']))")"
[[ "$N_SRC" -ge 1 ]] || { echo "expected sources: $ASK" >&2; exit 1; }

echo "== out-of-corpus refusal =="
EMPTY="$(curl -fsS -c "$COOKIE" -b "$COOKIE" -H "Content-Type: application/json" \
  -d '{"title":"empty"}' \
  "$BASE/api/threads")"
EID="$(echo "$EMPTY" | json_get "['id']")"
OOD="$(curl -fsS -c "$COOKIE" -b "$COOKIE" -H "Content-Type: application/json" \
  -d '{"content":"what is the capital of Mars?"}' \
  "$BASE/api/threads/${EID}/messages")"
OOD_ANS="$(echo "$OOD" | json_get "['assistant_message']['content']")"
[[ "$OOD_ANS" == "$CANNED" ]] || { echo "expected canned refusal: $OOD" >&2; exit 1; }

echo "smoke ok"
