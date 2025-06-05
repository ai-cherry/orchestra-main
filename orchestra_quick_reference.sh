#!/bin/bash
# Orchestra Quick Reference Commands

# Check system status
echo "=== System Status ==="
python3 implementation_checklist.py

# Run tests
echo "=== Running Tests ==="
python3 test_validation_framework.py

# Deploy infrastructure
echo "=== Deploy Infrastructure ==="
cd infrastructure && pulumi up

# Monitor logs
echo "=== Monitor Logs ==="
tail -f logs/orchestra.log

# Database console
echo "=== Database Console ==="
psql $DATABASE_URL
