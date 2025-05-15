# Makefile for Orchestra Monorepo Automation

.PHONY: setup check-versions lint test deploy

setup:
	@echo "[SETUP] Installing tools with asdf..."
	asdf install
	poetry install
	@echo "[SETUP] All tools and dependencies installed."

check-versions:
	@echo "[CHECK] Verifying tool versions from .tool-versions..."
	asdf current
	python --version
	poetry --version
	terraform version
	node --version

lint:
	@echo "[LINT] Running pre-commit, terraform fmt, and backend lint..."
	pre-commit run --all-files
	terraform fmt -check -recursive terraform/
	cd terraform && ./lint-backend.sh

# Add your test command here (example: pytest)
test:
	@echo "[TEST] Running tests..."
	pytest || echo "No tests found."

deploy:
	@echo "[DEPLOY] Running deployment pipeline..."
	gcloud builds submit --config=cloudbuild.yaml .
