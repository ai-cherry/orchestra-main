# Phase 1 Merge Plan: Repository Hygiene & Foundations

## Overview
This document outlines the process for merging `phase-1/repo-foundations` into `main`.

## Pre-Merge Checklist

### 1. Code Review Requirements
- [ ] All configuration files reviewed
- [ ] Python tooling configuration verified
- [ ] Node.js/pnpm configuration tested
- [ ] Docker Compose validated
- [ ] CI workflow syntax verified

### 2. Testing Requirements

#### Local Testing
```bash
# 1. Test Python tooling
poetry install
poetry run black --check .
poetry run isort --check-only .
poetry run ruff .

# 2. Test Node.js setup (after installing pnpm)
npm install -g pnpm
pnpm install
pnpm -r lint --if-present

# 3. Test Docker setup
docker-compose -f dev-compose.yml config
docker-compose -f dev-compose.yml up -d
docker-compose -f dev-compose.yml down

# 4. Test pre-commit hooks
poetry run pre-commit install
poetry run pre-commit run --all-files
```

#### CI Testing
- The new CI workflow will trigger on the PR
- Verify all jobs pass (Python, JavaScript, Docker, Docs)

### 3. Migration Tasks (Before Merge)

```bash
# Import existing Python dependencies
python scripts/import_reqs_to_poetry.py
poetry lock

# Verify no conflicts
poetry check
```

## Pull Request Process

### 1. Create PR
```bash
# Push latest changes
git push origin phase-1/repo-foundations

# Create PR via GitHub UI or CLI
gh pr create --title "Phase 1: Repository Hygiene & Foundations" \
  --body-file docs/phase-1-implementation.md \
  --base main \
  --head phase-1/repo-foundations
```

### 2. PR Description Template
```markdown
## Phase 1: Repository Hygiene & Foundations

### Summary
Implements comprehensive repository cleanup, dependency consolidation, and development tooling setup as part of the modernization initiative.

### Changes
- ✅ Python: Migrated to Poetry with Black/Ruff/isort configuration
- ✅ Node.js: Set up pnpm workspace with auto-peer-deps
- ✅ Docker: Traefik-based development stack (90xx ports)
- ✅ CI/CD: Path-filtered workflows with matrix testing
- ✅ Quality: Pre-commit hooks for all languages
- ✅ Developer Experience: Makefile with common commands

### Testing
- [ ] Local Python tests pass
- [ ] Local Node.js builds succeed
- [ ] Docker Compose starts cleanly
- [ ] Pre-commit hooks validated
- [ ] CI workflow passes

### Migration Notes
After merge, all developers need to:
1. Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
2. Install pnpm: `npm install -g pnpm`
3. Run: `make install && make pre-commit`

### Related Issues
- Addresses dependency conflicts
- Fixes port collision issues
- Establishes consistent code style
```

### 3. Review Process
1. **Self-review**: Verify all files are intended
2. **Automated checks**: Wait for CI to pass
3. **Team review**: Request review from at least 1 team member
4. **Address feedback**: Make any requested changes

## Merge Strategy

### Recommended: Squash and Merge
- Keeps main branch history clean
- All Phase 1 changes in single commit
- Preserves detailed history in PR

### Merge Commit Message
```
feat: implement Phase 1 repository hygiene and foundations (#PR_NUMBER)

- Configure Poetry for Python with modern tooling (Black/Ruff/isort)
- Set up pnpm workspace for Node.js monorepo management
- Create Docker Compose development environment with Traefik
- Add comprehensive pre-commit hooks and CI/CD pipeline
- Implement developer-friendly Makefile

BREAKING CHANGE: Developers must install Poetry and pnpm.
See docs/phase-1-implementation.md for migration instructions.
```

## Post-Merge Tasks

### 1. Immediate Actions
```bash
# 1. Update local main branch
git checkout main
git pull

# 2. Clean up feature branch
git branch -d phase-1/repo-foundations
git push origin --delete phase-1/repo-foundations

# 3. Update dependencies
make install
```

### 2. Team Communication
Send announcement to team:
```
Subject: [ACTION REQUIRED] Phase 1 Merged - Development Setup Update

Team,

Phase 1 (Repository Hygiene) has been merged. This brings:
- Poetry for Python dependency management
- pnpm for Node.js projects  
- New development commands via Makefile
- Pre-commit hooks for code quality

Required Actions:
1. Pull latest main branch
2. Install Poetry: https://python-poetry.org/docs/#installation
3. Install pnpm: npm install -g pnpm
4. Run: make install && make pre-commit

New Development Workflow:
- make install     # Install all dependencies
- make lint        # Run linters
- make format      # Auto-format code
- make docker-up   # Start dev environment

Questions? Check docs/phase-1-implementation.md or reach out.
```

### 3. Monitor for Issues
- Watch for CI failures on subsequent PRs
- Monitor Slack/Discord for developer questions
- Be ready to help with migration issues

### 4. Archive Legacy Code (Week After Merge)
Once team is stable on new setup:
```bash
make phase1-archive-legacy
```

## Rollback Plan

If critical issues arise:

### 1. Quick Rollback
```bash
# Revert the merge commit
git revert -m 1 <merge-commit-sha>
git push origin main
```

### 2. Fix Forward Approach (Preferred)
- Create hotfix branch from main
- Fix specific issues
- Fast-track PR with minimal review

### 3. Rollback Criteria
Only rollback if:
- CI/CD completely broken
- Developers cannot work
- Production deployments blocked

## Success Metrics

### Short Term (1 week)
- [ ] All developers successfully migrated
- [ ] CI passing rate > 95%
- [ ] No increase in build times
- [ ] Pre-commit adoption > 80%

### Medium Term (1 month)  
- [ ] Dependency conflicts eliminated
- [ ] Consistent code style across PRs
- [ ] Reduced onboarding time < 30 min
- [ ] No port collision issues

## Timeline

1. **Today**: Create PR, begin review
2. **Tomorrow**: Address feedback, run final tests
3. **Day 3**: Merge to main
4. **Day 4-7**: Support team migration
5. **Week 2**: Archive legacy code
6. **Week 4**: Measure success metrics 