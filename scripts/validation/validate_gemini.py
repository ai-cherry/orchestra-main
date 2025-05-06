#!/usr/bin/env python3
# validate_gemini.py - Validates Gemini Code Assist in the IDE

import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

def check_vscode_extensions():
    """Check if VS Code Gemini extension is installed"""
    try:
        result = subprocess.run(
            ["code", "--list-extensions"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            extensions = result.stdout.strip().split("\n")
            cloud_exts = [ext for ext in extensions if "google.cloud-code" in ext.lower()]
            gemini_exts = [ext for ext in extensions if "gemini" in ext.lower()]
            all_relevant = cloud_exts + gemini_exts
            
            return bool(all_relevant), f"Found Google Cloud/Gemini extensions: {all_relevant}"
        else:
            return False, f"Error listing VS Code extensions: {result.stderr}"
    except Exception as e:
        return False, f"Error checking VS Code extensions: {str(e)}"

def create_gemini_test_file():
    """Create a test Python file with a TODO comment for Gemini to help with"""
    test_file = Path("gemini_test.py")
    
    content = """
# Test file for Gemini Code Assist
import os

# TODO: Implement a function to list all Python files in a directory recursively

def main():
    print("Gemini Code Assist Test")

if __name__ == "__main__":
    main()
"""
    
    test_file.write_text(content)
    return test_file.exists(), str(test_file)

def check_gemini_env_vars():
    """Check if Gemini environment variables are set"""
    relevant_vars = [
        "VERTEX_AI_PROJECT",
        "VERTEX_AI_LOCATION",
        "GOOGLE_APPLICATION_CREDENTIALS"
    ]
    
    results = {}
    for var in relevant_vars:
        value = os.environ.get(var)
        results[var] = value is not None
    
    return results

def check_gemini_prompts_yaml():
    """Check if gemini_prompts.yaml exists"""
    prompts_file = Path("templates/gemini_prompts.yaml")
    
    if prompts_file.exists():
        try:
            with open(prompts_file, "r") as f:
                content = f.read()
            return True, "gemini_prompts.yaml exists and is readable"
        except Exception as e:
            return False, f"Error reading gemini_prompts.yaml: {str(e)}"
    else:
        return False, "gemini_prompts.yaml not found"

def check_cloudbuild_gemini_integration():
    """Check if Cloud Build configuration uses Gemini for code analysis"""
    try:
        with open("cloudbuild.yaml", "r") as f:
            content = f.read()
            
        has_gemini = "gemini" in content.lower()
        has_vertex = "vertex" in content.lower() or "aiplatform" in content.lower()
        
        if has_gemini and has_vertex:
            return True, "Cloud Build configuration includes Gemini and Vertex AI integration"
        elif has_gemini:
            return True, "Cloud Build configuration includes Gemini integration"
        elif has_vertex:
            return True, "Cloud Build configuration includes Vertex AI integration"
        else:
            return False, "Cloud Build configuration does not use Gemini or Vertex AI"
    except Exception as e:
        return False, f"Error checking Cloud Build configuration: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Validate Gemini Code Assist in IDE")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="GCP Location")
    args = parser.parse_args()
    
    print("### Gemini Code Assist IDE Integration")
    
    print("#### VS Code Extension Check")
    ext_ok, ext_msg = check_vscode_extensions()
    print(f"* VS Code Google Cloud extensions: {'✅' if ext_ok else '❌'}")
    print(f"  * {ext_msg}")
    
    print("\n#### Environment Variables")
    env_vars = check_gemini_env_vars()
    for var, exists in env_vars.items():
        print(f"* {var}: {'✅' if exists else '❌'}")
    
    print("\n#### Gemini Prompts Configuration")
    prompts_ok, prompts_msg = check_gemini_prompts_yaml()
    print(f"* Gemini prompts configuration: {'✅' if prompts_ok else '❌'}")
    print(f"  * {prompts_msg}")
    
    print("\n#### Cloud Build Integration")
    build_ok, build_msg = check_cloudbuild_gemini_integration()
    print(f"* Cloud Build Gemini integration: {'✅' if build_ok else '❌'}")
    print(f"  * {build_msg}")
    
    print("\n#### Test File Creation")
    file_ok, file_path = create_gemini_test_file()
    print(f"* Created test file: {'✅' if file_ok else '❌'}")
    print(f"  * {file_path}")
    
    print("\n#### Manual Verification Steps")
    print("To fully validate Gemini Code Assist:")
    print("1. Open the generated test file in VS Code")
    print("2. Place cursor on the TODO line")
    print("3. Trigger Gemini Code Assist (Ctrl+I or right-click > Gemini: Generate)")
    print("4. Verify that Gemini provides a code suggestion")
    print("5. Check if Code Assist can analyze existing files in the project")
    
    # Overall automatic checks
    all_auto_ok = ext_ok and file_ok and prompts_ok
    all_env_vars = all(env_vars.values())
    
    print(f"\n### Automated Gemini Code Assist Checks: {'✅' if all_auto_ok and all_env_vars else '❌'}")
    print("### Full validation requires manual interaction with the IDE")
    
    return 0 if all_auto_ok else 1

if __name__ == "__main__":
    sys.exit(main())
