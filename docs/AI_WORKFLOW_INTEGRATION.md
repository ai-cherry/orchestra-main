# AI Workflow Integration Guide

## 🔄 Complete AI-Assisted Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI-ASSISTED DEVELOPMENT FLOW                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PLANNING PHASE                                              │
│     └─ 📄 ai_context_planner.py                                │
│        └─ Checks existing tools first                          │
│        └─ Enforces simple solutions                            │
│                                                                  │
│  2. CODING PHASE                                                │
│     └─ 📄 ai_context_coder.py                                  │
│        └─ Provides correct patterns                            │
│        └─ Shows what to import/reuse                           │
│                                                                  │
│  3. REVIEW PHASE                                                │
│     ├─ 📄 ai_context_reviewer.py (Manual review)               │
│     └─ 🔧 scripts/ai_code_reviewer.py (Automated)              │
│        └─ Catches anti-patterns                                │
│                                                                  │
│  4. DEBUG PHASE (if needed)                                     │
│     └─ 📄 ai_context_debugger.py                               │
│        └─ Common issues & solutions                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 File Relationships

### **Context Files (Preventive)**

- `ai_context_planner.py` - Before you start
- `ai_context_coder.py` - While coding
- `ai_context_reviewer.py` - For code review
- `ai_context_debugger.py` - When things break

### **Automation Tools (Detective)**

- `scripts/ai_code_reviewer.py` - Automated anti-pattern detection
- `scripts/config_validator.py` - Configuration validation
- `scripts/health_monitor.py` - Service health checks
- `scripts/orchestra.py` - Unified CLI

### **Documentation (Reference)**

- `docs/AI_CODING_STANDARDS.md` - Comprehensive standards
- `docs/PROJECT_STRUCTURE.md` - Where everything lives
- `AI_CONTEXT_FILES.md` - Quick reference for context files
- `.cursorrules` - Editor-specific rules

## 🎯 Typical Workflow Example

### **Scenario: Adding Email Notifications**

```bash
# 1. PLAN
"Read ai_context_planner.py and help me plan email notifications"
# AI checks existing notification system first

# 2. CREATE CHECKPOINT
make before-ai-coding

# 3. CODE
"Read ai_context_coder.py and implement email notifications"
# AI uses existing patterns, correct imports

# 4. AUTOMATED REVIEW
make ai-review-changes
# Catches any anti-patterns

# 5. MANUAL REVIEW (if needed)
"Read ai_context_reviewer.py and review this implementation"

# 6. VALIDATE
make validate

# 7. DEBUG (if issues)
"Read ai_context_debugger.py and help fix this error"
```

## ⚖️ Balance & Recommendations

### **Current System (Optimal)**

✅ **4 Context Files** - One per development phase

- Clear purpose for each
- No overlap or confusion
- Easy to remember when to use each

### **Why Not More Files?**

We considered but decided against:

- ❌ **Testing Context** - Already covered in coder/reviewer
- ❌ **Infrastructure Context** - Handled by custom_instructions
- ❌ **Strategy Context** - Too abstract, not actionable

### **Key Principle: Simple > Complex**

The current 4-file system is:

- Easy to understand
- Maps to natural development phases
- Doesn't overwhelm with choices
- Covers all necessary scenarios

## 🛡️ Integration Points

### **Makefile Targets**

```bash
make before-ai-coding    # Checkpoint before AI work
make ai-review-changes   # Review git changes
make after-ai-coding     # Full validation
make validate           # Complete validation suite
```

### **Git Workflow**

1. Create checkpoint before AI coding
2. Use appropriate context file
3. Commit with descriptive message
4. Run automated checks
5. Push only after validation

### **CI/CD Integration**

The `ai_code_reviewer.py` can be integrated into:

- Pre-commit hooks
- GitHub Actions
- Merge request pipelines

## 📊 Success Metrics

Your AI-assisted code should:

- ✅ Pass `make ai-review-changes` with 0 errors
- ✅ Use existing tools from `scripts/`
- ✅ Follow patterns from context files
- ✅ Work on Python 3.10
- ✅ Have no Docker/Poetry dependencies
- ✅ Be simpler than your first instinct

## 🚦 Quick Decision Tree

```
Need to add a feature?
├─ Read ai_context_planner.py first
├─ Does it already exist? → Extend it
└─ Really need new? → Follow ai_context_coder.py

Got an error?
├─ Read ai_context_debugger.py
├─ Check common issues
└─ Use debugging workflow

Reviewing code?
├─ Run make ai-review-changes first
└─ Then read ai_context_reviewer.py for manual review
```

---

**Remember: The goal is consistency and simplicity. When in doubt, check existing patterns!**
