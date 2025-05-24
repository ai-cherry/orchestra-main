#!/bin/bash
# update_reqs.sh: Update requirements.txt with current venv packages
set -e
source ~/orchestra-main/venv/bin/activate
pip freeze | grep -v "pkg-resources" > requirements.txt
echo "requirements.txt updated from current environment."
