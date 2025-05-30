#!/bin/bash
set -e
CACHE_DIR="$HOME/.cache/pip"
if [ -d "$CACHE_DIR" ]; then
  echo "Using cached wheels"
  pip install --no-index --find-links "$CACHE_DIR" -r requirements/base.txt
else
  echo "Cache not found; attempting normal install"
  pip install -r requirements/base.txt
fi
