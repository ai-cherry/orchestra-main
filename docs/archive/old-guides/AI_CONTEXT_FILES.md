# AI Context Files Reference

## 🎯 Quick Copy-Paste Guide

Use these filenames in your AI prompts to ensure consistency:

### **Planning a Feature/Change**

```
Read ai_context_planner.py
```

### **Writing Code**

```
Read ai_context_coder.py
```

### **Reviewing Code**

```
Read ai_context_reviewer.py
```

### **Debugging Issues**

```
Read ai_context_debugger.py
```

## 📋 Usage Examples

### Planning Example

> "Read ai_context_planner.py and help me plan a feature to add email notifications"

### Coding Example

> "Read ai_context_coder.py and implement a function to parse CSV files"

### Review Example

> "Read ai_context_reviewer.py and review these changes: [paste code]"

### Debug Example

> "Read ai_context_debugger.py and help debug this error: [paste error]"

## 🔄 Combined Usage

For complex tasks, you can use multiple contexts:

```
Read ai_context_planner.py and ai_context_coder.py
```

## 🛡️ What These Files Do

- **Prevent AI from suggesting Docker, Poetry, or complex patterns**
- **Ensure Python 3.10 compatibility (not 3.11+)**
- **Guide toward existing tools in scripts/**
- **Enforce project standards automatically**
- **Provide role-specific guidance**

## ❓ Why Only 4 Files?

We intentionally keep it simple:

- **No Testing Context** - Testing patterns are covered in `ai_context_coder.py` (shows how to validate) and `ai_context_reviewer.py` (what to check)
- **No Infrastructure Context** - GCP/Pulumi patterns are already in your custom instructions
- **No Strategy Context** - Too abstract; planning context handles high-level decisions

The 4-file system maps cleanly to development phases: Plan → Code → Review → Debug

## ✅ Validation

After AI generates code, always run:

```bash
make ai-review-changes    # Review git changes
make validate            # Full validation
```

## 📁 File Locations

All context files are in the project root:

- `ai_context_planner.py` - Planning guidance
- `ai_context_coder.py` - Coding patterns
- `ai_context_reviewer.py` - Review checklist
- `ai_context_debugger.py` - Debug workflows

---

**Remember: These files are your "no-nonsense fallback" - use them every time!**
