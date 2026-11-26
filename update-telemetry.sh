#!/bin/bash
# Daily token telemetry refresh: render SVGs from local token monitor export, commit if changed, push.
cd "$(dirname "$0")"
python scripts/render_profile.py || exit 1
git add README.md assets/harness-*.svg assets/*-tokens.svg assets/*-cost.svg assets/activity.svg
if git diff --cached --quiet; then
  echo "sin cambios — nada que commitear"
  exit 0
fi
git -c user.name="jseramn" -c user.email="contacto@jseramn.tech" commit -q -m "chore(telemetry): token card refresh $(date +%F)"
git push origin main 2>&1 | tail -1
echo "telemetry pushed $(date -Iseconds)"
