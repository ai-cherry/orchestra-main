#!/bin/bash
# orchestra_automation.sh - Simple launcher for Orchestra automation tools

# Make scripts executable
chmod +x run_pre_deployment_automated.sh
chmod +x analyze_code_duplication.py

echo "Orchestra Automation Tools"
echo "=========================="
echo ""
echo "1. Run Pre-Deployment Verification"
echo "2. Analyze Code Duplication"
echo ""
read -p "Select an option (1 or 2): " option

case $option in
  1)
    ./run_pre_deployment_automated.sh
    ;;
  2)
    echo ""
    read -p "Enter directory to analyze (default: core): " path
    path=${path:-"core"}
    ./analyze_code_duplication.py --path "$path"
    ;;
  *)
    echo "Invalid option"
    ;;
esac
