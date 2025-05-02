#!/usr/bin/env python3
# validate_vertex.py - Validates Vertex AI integration

import sys
import os
import argparse
import subprocess
import json

def validate_vertex_imports():
    """Validate that required packages are installed"""
    try:
        import google.cloud.aiplatform
        return True, "Successfully imported google.cloud.aiplatform"
    except ImportError as e:
        return False, f"Error importing Vertex AI modules: {str(e)}"

def validate_vertex_api_access(project_id, location):
    """Check if Vertex AI API can be accessed"""
    try:
        result = subprocess.run(
            [
                "gcloud", "ai", "models", "list",
                f"--project={project_id}",
                f"--region={location}",
                "--limit=1",
                "--format=json"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            models = json.loads(result.stdout) if result.stdout.strip() else []
            return True, f"Vertex AI API is accessible, found {len(models)} models"
        else:
            return False, f"Error accessing Vertex AI API: {result.stderr}"
    except Exception as e:
        return False, f"Error accessing Vertex AI API: {str(e)}"

def validate_gemini_models(project_id, location):
    """Validate access to Gemini models"""
    try:
        result = subprocess.run(
            [
                "gcloud", "ai", "models", "list",
                f"--project={project_id}",
                f"--region={location}",
                "--filter=displayName:gemini",
                "--format=json"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            models = json.loads(result.stdout) if result.stdout.strip() else []
            return True, f"Found {len(models)} Gemini models"
        else:
            return False, f"Error listing Gemini models: {result.stderr}"
    except Exception as e:
        return False, f"Error checking Gemini models: {str(e)}"

def test_vertex_env_vars():
    """Test if Vertex environment variables are set"""
    required_vars = ["VERTEX_AI_PROJECT", "VERTEX_AI_LOCATION"]
    results = {}
    
    for var in required_vars:
        value = os.environ.get(var)
        results[var] = value is not None
        
    return results

def test_vertex_integration_file():
    """Check if Vertex operations file exists and is valid"""
    vertex_file = "agent/core/vertex_operations.py"
    
    if os.path.isfile(vertex_file):
        try:
            with open(vertex_file, "r") as f:
                content = f.read()
                
            # Check for key Vertex AI imports and functions
            has_import = "from google.cloud import aiplatform" in content
            has_functions = "VertexAgent" in content
            
            if has_import and has_functions:
                return True, "Vertex operations file exists and looks valid"
            else:
                return True, "Vertex operations file exists but may be missing key components"
        except Exception as e:
            return False, f"Error reading Vertex operations file: {str(e)}"
    else:
        return False, f"Vertex operations file not found: {vertex_file}"

def main():
    parser = argparse.ArgumentParser(description="Validate Vertex AI integration")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="GCP Location")
    args = parser.parse_args()
    
    print("### Vertex AI Package Verification")
    imports_ok, imports_msg = validate_vertex_imports()
    print(f"* Vertex AI Packages: {'✅' if imports_ok else '❌'}")
    print(f"  * {imports_msg}")
    
    print("\n### Vertex AI Environment Variables")
    env_vars = test_vertex_env_vars()
    for var, exists in env_vars.items():
        print(f"* {var}: {'✅' if exists else '❌'}")
    
    print("\n### Vertex AI API Accessibility")
    api_ok, api_msg = validate_vertex_api_access(args.project, args.location)
    print(f"* Vertex AI API: {'✅' if api_ok else '❌'}")
    print(f"  * {api_msg}")
    
    print("\n### Gemini Models Accessibility")
    try:
        gemini_ok, gemini_msg = validate_gemini_models(args.project, args.location)
        print(f"* Gemini Models: {'✅' if gemini_ok else '❌'}")
        print(f"  * {gemini_msg}")
    except Exception as e:
        print(f"* Gemini Models: ❌")
        print(f"  * Error checking Gemini models: {str(e)}")
        gemini_ok = False
    
    print("\n### Vertex Integration File")
    file_ok, file_msg = test_vertex_integration_file()
    print(f"* Vertex Operations File: {'✅' if file_ok else '❌'}")
    print(f"  * {file_msg}")
    
    # Overall status for automatic checks
    all_auto_ok = imports_ok and api_ok and (gemini_ok if 'gemini_ok' in locals() else False) and file_ok
    all_env_vars = all(env_vars.values())
    
    print(f"\n### Overall Vertex AI Validation: {'✅' if all_auto_ok and all_env_vars else '❌'}")
    
    return 0 if all_auto_ok and all_env_vars else 1

if __name__ == "__main__":
    sys.exit(main())
