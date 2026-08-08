#!/usr/bin/env bash
# Sync Odysseus upstream into this ShadowRealm fork with minimal friction.
#
# Usage:
#   ./scripts/sync_odysseus_upstream.sh              # fetch + report
#   ./scripts/sync_odysseus_upstream.sh --merge       # merge upstream/main into current branch
#   ./scripts/sync_odysseus_upstream.sh --rebase      # rebase current branch onto upstream/main
#
# Expects remote "upstream" → https://github.com/pewdiepie-archdaemon/odysseus.git
# (or set ODYSSEUS_UPSTREAM_URL). ShadowRealm-owned code lives under shadowrealm/;
# Odysseus touchpoints are marked # SHADOWREALM: — resolve those first on conflicts.

set -euo pipefail

UPSTREAM_URL="${ODYSSEUS_UPSTREAM_URL:-https://github.com/pewdiepie-archdaemon/odysseus.git}"
UPSTREAM_REF="${ODYSSEUS_UPSTREAM_REF:-main}"
MODE="report"

for arg in "$@"; do
  case "$arg" in
    --merge) MODE="merge" ;;
    --rebase) MODE="rebase" ;;
    --help|-h)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

cd "$(git rev-parse --show-toplevel)"

if ! git remote get-url upstream >/dev/null 2>&1; then
  echo "Adding upstream remote → $UPSTREAM_URL"
  git remote add upstream "$UPSTREAM_URL"
else
  echo "upstream remote: $(git remote get-url upstream)"
fi

echo "Fetching upstream..."
git fetch upstream --tags

LOCAL_SHA=$(git rev-parse HEAD)
UPSTREAM_SHA=$(git rev-parse "upstream/${UPSTREAM_REF}")
echo "HEAD:              $LOCAL_SHA ($(git branch --show-current))"
echo "upstream/$UPSTREAM_REF: $UPSTREAM_SHA"

AHEAD=$(git rev-list --count "upstream/${UPSTREAM_REF}..HEAD" 2>/dev/null || echo "?")
BEHIND=$(git rev-list --count "HEAD..upstream/${UPSTREAM_REF}" 2>/dev/null || echo "?")
echo "Commits ahead of upstream: $AHEAD"
echo "Commits behind upstream:   $BEHIND"

echo
echo "ShadowRealm-owned paths (prefer keeping ours on conflict):"
echo "  shadowrealm/"
echo "  skills/analyze_project.md skills/fix_and_verify.md skills/review_before_ship.md"
echo
echo "Thin Odysseus hooks to re-check after sync:"
git grep -n "SHADOWREALM" -- app.py routes/chat_routes.py src/agent_loop.py AGENTS.md 2>/dev/null || true

if [[ "$MODE" == "report" ]]; then
  echo
  echo "Report only. Re-run with --merge or --rebase when ready."
  exit 0
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree not clean — commit or stash before sync." >&2
  exit 1
fi

if [[ "$MODE" == "merge" ]]; then
  echo "Merging upstream/${UPSTREAM_REF}..."
  git merge --no-ff "upstream/${UPSTREAM_REF}" -m "merge: Odysseus upstream/${UPSTREAM_REF} into ShadowRealm"
elif [[ "$MODE" == "rebase" ]]; then
  echo "Rebasing onto upstream/${UPSTREAM_REF}..."
  git rebase "upstream/${UPSTREAM_REF}"
fi

echo
echo "Sync step finished. Next:"
echo "  1. Resolve any conflicts — keep shadowrealm/ ours; re-apply # SHADOWREALM: hooks if dropped."
echo "  2. pytest tests/test_model_router.py -q"
echo "  3. Smoke: uvicorn app:app + Ollama chat"
