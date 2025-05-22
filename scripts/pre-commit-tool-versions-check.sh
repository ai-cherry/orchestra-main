#!/usr/bin/env bash
set -euo pipefail

# Pre-commit hook: Check for .tool-versions drift

if ! command -v asdf &>/dev/null; then
  echo "asdf not found. Skipping .tool-versions check."
  exit 0
fi

# Check if all tools match .tool-versions
FAILED=0
while read -r tool version; do
  [ -z "$tool" ] && continue
  current=$(asdf current "$tool" | awk '{print $2}')
  if [ "$current" != "$version" ]; then
    echo "[ERROR] $tool version mismatch: .tool-versions=$version, current=$current"
    FAILED=1
  fi
done < <(grep -v '^#' .tool-versions | grep -v '^$')

if [ $FAILED -ne 0 ]; then
  echo "[FAIL] asdf tool versions do not match .tool-versions. Run 'asdf install'."
  exit 1
fi

exit 0
