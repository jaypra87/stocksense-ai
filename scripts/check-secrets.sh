#!/usr/bin/env bash
# Scan the working tree (and optionally full git history) for committed secrets.
#
# Run before pushing, or wire it in as a pre-commit hook:
#   ln -s ../../scripts/check-secrets.sh .git/hooks/pre-commit
#
# Usage:
#   scripts/check-secrets.sh            # staged + tracked files
#   scripts/check-secrets.sh --history  # every blob in every commit (slower)
set -uo pipefail

RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; NC=$'\033[0m'

# Patterns worth failing a commit over. Deliberately narrow: a scanner that
# cries wolf gets disabled, and a disabled scanner catches nothing.
PATTERNS=(
  'sk-[A-Za-z0-9]{20,}'                      # OpenAI-style keys
  'AKIA[0-9A-Z]{16}'                         # AWS access key id
  'ghp_[A-Za-z0-9]{36}'                      # GitHub personal access token
  'gh[pousr]_[A-Za-z0-9]{36}'                # other GitHub token classes
  'xox[baprs]-[A-Za-z0-9-]{10,}'             # Slack tokens
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'       # private keys
  'postgres(ql)?://[^:]+:[^@/ ]{8,}@'        # DB URL with an inline password
  'redis(s)?://[^:]*:[^@/ ]{8,}@'            # Redis URL with a password
)

# Files that are *supposed* to contain placeholder-looking values.
EXCLUDE_RE='(^|/)(\.env\.example|.*\.example|package-lock\.json|.*\.lock)$|(^|/)(node_modules|\.venv|\.next|\.git)/|(^|/)scripts/check-secrets\.sh$'

fail=0

scan_blob() {  # $1 = label, $2 = content on stdin
  local label="$1" content; content="$(cat)"
  for pattern in "${PATTERNS[@]}"; do
    # `-e` is required: the private-key pattern starts with dashes, which grep
    # would otherwise read as options.
    if match=$(printf '%s' "$content" | grep -nEo -e "$pattern" | head -3); then
      [ -z "$match" ] && continue
      printf '%s✗ possible secret in %s%s\n' "$RED" "$label" "$NC"
      printf '    %s\n' "$match"
      fail=1
    fi
  done
}

if [ "${1:-}" = "--history" ]; then
  echo "Scanning full git history…"
  while read -r sha path; do
    printf '%s' "$path" | grep -qE "$EXCLUDE_RE" && continue
    git cat-file -p "$sha" 2>/dev/null | scan_blob "$path (blob $sha)"
  done < <(git rev-list --all --objects | awk 'NF==2 {print $1, $2}')
else
  echo "Scanning tracked files…"
  while read -r path; do
    printf '%s' "$path" | grep -qE "$EXCLUDE_RE" && continue
    [ -f "$path" ] || continue
    scan_blob "$path" < "$path"
  done < <(git ls-files)

  # A tracked .env is a finding on its own, whatever it contains.
  if git ls-files --error-unmatch '.env' 'backend/.env' 'frontend/.env.local' >/dev/null 2>&1; then
    printf '%s✗ an environment file is tracked by git%s\n' "$RED" "$NC"
    fail=1
  fi
fi

if [ "$fail" -eq 0 ]; then
  printf '%s✓ no secrets detected%s\n' "$GREEN" "$NC"
else
  printf '\nRemove the secret, rotate it, and re-run. Rotation is the part that\n'
  printf 'actually matters: anything that reached a remote must be considered public.\n'
fi
exit "$fail"
