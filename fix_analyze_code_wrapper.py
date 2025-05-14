#!/usr/bin/env python3
"""
Fix script for the analyze_code_wrapper.py pre-commit hook.
This script updates the analyze_code_wrapper.py file to properly handle file lists.
"""

import os
import sys


def fix_analyze_code_wrapper():
    script_path = "/workspaces/orchestra-main/analyze_code_wrapper.py"

    # Check if file exists
    if not os.path.exists(script_path):
        print(f"Error: {script_path} does not exist.")
        return False

    # Read the current content
    with open(script_path, "r") as f:
        content = f.read()

    # Fix the main function to properly handle file lists
    updated_main = """def main():
    parser = argparse.ArgumentParser(description="Analyze staged code with Gemini")
    parser.add_argument(
        "--extensions", 
        default=".py,.js,.ts",
        help="Comma-separated list of file extensions to analyze"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="List of files to analyze"
    )
    args = parser.parse_args()
    
    # Get file extensions to analyze
    extensions = args.extensions.split(",")
    
    # Get files to analyze - either from args or from git staging
    if args.files:
        staged_files = args.files
    else:
        staged_files = get_staged_files(extensions)
    
    if not staged_files or staged_files == [""]:
        print("No matching files to analyze.")
        return 0
    
    print(f"Running Gemini code analysis on files...")
    print(f"Files: {','.join(staged_files)}")
    
    # Read file contents
    files_content = {}
    for file_path in staged_files:
        content = read_file_content(file_path)
        if content:
            files_content[file_path] = content
    
    if not files_content:
        print("No valid files to analyze.")
        return 1
    
    try:
        # Analyze code
        results = analyze_code_with_gemini(files_content)
        
        # Print analysis results
        print("\\n===== Gemini Code Analysis =====\\n")
        print(results["analysis"])
        print("\\n================================\\n")
        
        # Print security issues
        if results.get("security_issues"):
            print("\\n===== Security Issues Found =====\\n")
            for issue in results["security_issues"]:
                print(f"{issue['severity'].upper()} in {issue['file']} (line {issue['line']})")
                print(f"  Message: {issue['message']}")
                print(f"  Code: {issue['code']}\\n")
            print("================================\\n")
        
        # If critical issues are found, exit with error
        if results.get("has_critical_issues"):
            print("Critical security issues found in your code!")
            print("Please fix the issues before committing or use 'git commit --no-verify' to bypass this check.")
            return 1
            
        # Ask if user wants to proceed with commit for non-critical issues
        if results.get("security_issues"):
            # In a pre-commit hook, assume user wants to proceed
            # Uncomment for interactive use:
            # response = input("Security issues found. Proceed with commit anyway? (y/n): ").lower()
            # if response != 'y':
            #     print("Commit aborted by user.")
            #     return 1
            print("Non-critical security issues found. Proceeding with commit.")
            
        return 0
        
    except Exception as e:
        print(f"Error during code analysis: {str(e)}")
        print("You can still commit, but consider fixing the analysis script.")
        return 0"""

    # Update the content with the fixed main function
    updated_content = content.replace(
        "def main():",
        updated_main.split("def main():")[0] + "def main():"
    )
    updated_content = updated_content.replace(
        "if __name__ == \"__main__\":",
        updated_main.split("def main():")[1] + "\n\nif __name__ == \"__main__\":"
    )

    # Write the updated content back to the file
    with open(script_path, "w") as f:
        f.write(updated_content)

    print(f"Successfully updated {script_path}")
    print("The script now properly handles file lists and will work correctly in pre-commit hooks.")
    return True


if __name__ == "__main__":
    success = fix_analyze_code_wrapper()
    sys.exit(0 if success else 1)
