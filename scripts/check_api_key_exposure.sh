#!/bin/bash
# Check for exposed API keys in the repository

echo "🔍 Checking for exposed API keys..."
echo "=================================="

# Common API key patterns
patterns=(
    "sk_[a-zA-Z0-9]{32,}"
    "pk_[a-zA-Z0-9]{32,}"
    "ELEVENLABS_API_KEY=sk_[a-zA-Z0-9]"
    "OPENAI_API_KEY=sk-[a-zA-Z0-9]"
)

found_issues=false

# Check each pattern
for pattern in "${patterns[@]}"; do
    echo -n "Checking for pattern: $pattern ... "
    
    # Search for the pattern, excluding safe directories and files
    results=$(grep -r -E "$pattern" . \
        --exclude-dir=.git \
        --exclude-dir=venv \
        --exclude-dir=node_modules \
        --exclude-dir=.env \
        --exclude=.env \
        --exclude=.env.local \
        --exclude="*.log" \
        --exclude="check_api_key_exposure.sh" \
        2>/dev/null | \
        grep -v "your_api_key_here" | \
        grep -v "your_actual_key_here" | \
        grep -v "your-.*-key" | \
        grep -v "example" | \
        grep -v "dummy" | \
        grep -v "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | \
        grep -v "placeholder" | \
        grep -v "test")
    
    if [ -n "$results" ]; then
        echo "❌ FOUND!"
        echo "$results"
        found_issues=true
    else
        echo "✅ Clean"
    fi
done

echo ""
echo "Checking .env file status..."
if [ -f .env ]; then
    if git ls-files --error-unmatch .env 2>/dev/null; then
        echo "❌ WARNING: .env file is tracked by git!"
        found_issues=true
    else
        echo "✅ .env file exists but is properly gitignored"
    fi
else
    echo "ℹ️  No .env file found"
fi

echo ""
echo "Checking for hardcoded ElevenLabs key specifically..."
# Check for ElevenLabs API keys that look real (start with sk_ and have 40+ chars)
if grep -r -E "sk_[a-zA-Z0-9]{40,}" . --exclude-dir=.git --exclude-dir=venv --exclude=.env --exclude=check_api_key_exposure.sh 2>/dev/null | grep -v "your" | grep -v "example"; then
    echo "❌ CRITICAL: Found potential hardcoded API key!"
    found_issues=true
else
    echo "✅ No hardcoded API keys found"
fi

echo ""
if [ "$found_issues" = true ]; then
    echo "❌ SECURITY ISSUES FOUND! Please fix before committing."
    exit 1
else
    echo "✅ No exposed API keys found. Safe to commit!"
    exit 0
fi 