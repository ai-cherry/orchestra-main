#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# fix_poetry_and_workspace.sh
#  › Run inside a Codespace (recovery or standard). It:
#    1) Masks Poetry 2.x in user-local bin
#    2) Installs Poetry 1.8.2 via pipx (global path)
#    3) Appends PATH export to .devcontainer/Dockerfile if missing
#    4) Writes a minimal workspace-aware root pyproject.toml
#    5) Deletes service-local .venv try.lock cruft
#    6) Generates a single workspace lock & venv
#    7) Prints a quick sanity check
###############################################################################

echo "🔍  Step 1 | Remove stray Poetry 2.x from user-local bin…"
if [[ -f /vscode/.local/bin/poetry ]]; then
  sudo mv /vscode/.local/bin/poetry /vscode/.local/bin/poetry-2x.bak
  echo "    → moved to poetry-2x.bak"
else
  echo "    → no user-local Poetry found (good)"
fi

echo "🚀  Step 2 | Install Poetry 1.8.2 via pipx…"
pipx install --force "poetry==1.8.2"
echo "    → $(poetry --version)"

echo "🛠  Step 3 | Ensure global path is in Dockerfile…"
DOCKERFILE=".devcontainer/Dockerfile"
if ! grep -q '/usr/local/py-utils/bin' "$DOCKERFILE"; then
  echo 'ENV PATH="/usr/local/py-utils/bin:${PATH}"' | sudo tee -a "$DOCKERFILE" >/dev/null
  echo "    → PATH line appended to $DOCKERFILE"
else
  echo "    → PATH already present"
fi

echo "📜  Step 4 | Write minimal root pyproject.toml (workspace)…"
ROOT_PY=pyproject.toml
cat > "$ROOT_PY" <<'TOML'
[tool.poetry]
name = "ai-orchestra-root"
version = "0.0.0"
description = "Workspace root – not published"

[tool.poetry.dependencies]
python = ">=3.11,<4.0"

[tool.poetry.workspace]
members = ["services/*", "packages/*"]
TOML
echo "    → $ROOT_PY written/overwritten"

echo "🧹  Step 5 | Delete service-local .venv and lock files…"
find services packages -name ".venv" -prune -exec rm -rf {} + 2>/dev/null || true
find services packages -name "poetry.lock" -delete 2>/dev/null || true

echo "🔄  Step 6 | Generate workspace venv & lock…"
poetry env use 3.11
poetry install --no-root --sync

echo "✅  Step 7 | Sanity check…"
poetry --version
poetry debug info | grep -E 'System|Virtualenv'
python -V
poetry run python - <<'PY'
import sys, backoff, pathlib
print("Python  :", sys.version.split()[0])
print("backoff :", backoff.__version__)
print("Venv    :", pathlib.Path(sys.prefix).as_posix())
PY

cat <<'MSG'

🎉  All done!

• Commit the modified Dockerfile, root pyproject.toml, and poetry.lock:
      git add .devcontainer/Dockerfile pyproject.toml poetry.lock
      git commit -m "chore(devcontainer): pin Poetry 1.8.2 and define workspace"

• Push and click **“Rebuild Container”** in Codespaces.

The next build should start in **standard mode**, with a single
workspace venv and Poetry 1.8.x.  You can then safely:

      poetry add -C services/admin-api google-cloud-aiplatform@^1.24

and continue wiring the live Vertex AI backend.

MSG
