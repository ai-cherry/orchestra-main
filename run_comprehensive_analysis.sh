#!/bin/bash

echo "Running Comprehensive Codebase Analysis..."
echo "========================================"

# Make scripts executable
chmod +x comprehensive_codebase_analyzer.py
chmod +x automated_syntax_fixer.py

# Run the comprehensive analyzer
echo -e "\n1. Running comprehensive codebase analysis..."
python3 comprehensive_codebase_analyzer.py

# Check if analysis report was created
if [ -f "comprehensive_analysis_report_*.json" ]; then
    echo -e "\n✓ Analysis report generated successfully"
    
    # Display summary
    echo -e "\n2. Analysis Summary:"
    python3 -c "
import json
import glob

# Find the latest report
reports = glob.glob('comprehensive_analysis_report_*.json')
if reports:
    latest_report = sorted(reports)[-1]
    with open(latest_report, 'r') as f:
        data = json.load(f)
    
    print(f'Total Issues: {data[\"summary\"][\"total_issues\"]}')
    print(f'Critical: {data[\"summary\"][\"critical\"]}')
    print(f'High: {data[\"summary\"][\"high\"]}')
    print(f'Medium: {data[\"summary\"][\"medium\"]}')
    print(f'Low: {data[\"summary\"][\"low\"]}')
    
    print('\nTop Patterns:')
    for pattern in data['patterns'][:3]:
        print(f'  - {pattern[\"pattern\"]}: {pattern[\"count\"]} occurrences')
"
else
    echo "✗ Failed to generate analysis report"
    exit 1
fi

echo -e "\n3. Next Steps:"
echo "   - Run './fix_syntax_errors.sh' to fix all Python indentation errors"
echo "   - Run './security_scan.sh' to scan for hardcoded credentials"
echo "   - Run './dependency_check.sh' to validate dependencies"

echo -e "\nAnalysis complete!"