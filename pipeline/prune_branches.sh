#!/usr/bin/env bash
# Delete remote daily digest branches (daily/<topic>/<YYYY-MM-DD>) older than N days (default 7).
# Usage: bash pipeline/prune_branches.sh [days]
set -euo pipefail
days="${1:-7}"
cutoff=$(date -u -d "-${days} days" +%F)
git ls-remote --heads origin 'refs/heads/daily/*' | awk '{print $2}' | sed 's#refs/heads/##' | while read -r br; do
  d="${br##*/}"
  if [[ "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ && "$d" < "$cutoff" ]]; then
    echo "delete $br"
    git push -q origin --delete "$br"
  fi
done
