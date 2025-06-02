#!/usr/bin/env python3
"""
Security Audit Script for Orchestra AI
Performs comprehensive security scans on all Python dependencies
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str):
    """Print success message in green"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text: str):
    """Print warning message in yellow"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text: str):
    """Print error message in red"""
    print(f"{RED}✗ {text}{RESET}")


def check_pip_audit_installed() -> bool:
    """Check if pip-audit is installed"""
    try:
        subprocess.run(["pip-audit", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_security_tools():
    """Install required security tools"""
    print_header("Installing Security Tools")
    
    tools = ["pip-audit", "safety"]
    for tool in tools:
        print(f"Installing {tool}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", tool], 
                         capture_output=True, check=True)
            print_success(f"{tool} installed successfully")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install {tool}: {e}")
            return False
    return True


def scan_requirements_file(req_file: Path) -> Tuple[bool, List[Dict], str]:
    """
    Scan a single requirements file for vulnerabilities
    Returns: (has_vulnerabilities, vulnerabilities_list, error_message)
    """
    print(f"\nScanning {req_file}...")
    
    # Create temporary file for JSON output
    json_output = req_file.parent / f".{req_file.stem}_audit.json"
    
    try:
        # Run pip-audit with JSON output
        result = subprocess.run(
            ["pip-audit", "--requirement", str(req_file), "--format", "json", 
             "--output", str(json_output)],
            capture_output=True,
            text=True
        )
        
        if json_output.exists():
            with open(json_output, 'r') as f:
                audit_data = json.load(f)
            json_output.unlink()  # Clean up temp file
            
            vulnerabilities = audit_data.get("vulnerabilities", [])
            if vulnerabilities:
                return True, vulnerabilities, ""
            else:
                return False, [], ""
        else:
            # Check for resolution errors
            if "ResolutionImpossible" in result.stderr:
                return None, [], "Dependency conflict detected"
            else:
                return None, [], result.stderr
                
    except Exception as e:
        return None, [], str(e)


def scan_all_requirements() -> Dict[str, Dict]:
    """Scan all requirements files in the project"""
    print_header("Comprehensive Security Scan")
    
    # Find all requirements files
    req_files = [
        Path("requirements/base.txt"),
        Path("requirements/dev.txt"),
        Path("requirements/production/requirements.txt"),
        Path("requirements/unified.txt"),
        Path("requirements/pay_ready.txt"),
        Path("requirements/monitoring.txt"),
        Path("requirements/superagi.txt"),
    ]
    
    # Add any requirements*.txt in root
    req_files.extend(Path(".").glob("requirements*.txt"))
    
    results = {}
    total_vulns = 0
    
    for req_file in req_files:
        if not req_file.exists():
            continue
            
        has_vulns, vulns, error = scan_requirements_file(req_file)
        
        if has_vulns is None:
            print_warning(f"{req_file}: {error}")
            results[str(req_file)] = {"status": "error", "error": error}
        elif has_vulns:
            vuln_count = len(vulns)
            total_vulns += vuln_count
            print_error(f"{req_file}: Found {vuln_count} vulnerabilities")
            results[str(req_file)] = {
                "status": "vulnerable",
                "count": vuln_count,
                "vulnerabilities": vulns
            }
        else:
            print_success(f"{req_file}: No vulnerabilities found")
            results[str(req_file)] = {"status": "secure", "count": 0}
    
    return results, total_vulns


def generate_report(results: Dict, total_vulns: int):
    """Generate a security audit report"""
    print_header("Security Audit Report")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_file = Path(f"security_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    report = {
        "timestamp": timestamp,
        "total_vulnerabilities": total_vulns,
        "scanned_files": len(results),
        "results": results
    }
    
    # Save detailed JSON report
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Detailed report saved to: {report_file}")
    
    # Print summary
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Timestamp: {timestamp}")
    print(f"  Files scanned: {len(results)}")
    print(f"  Total vulnerabilities: {total_vulns}")
    
    if total_vulns == 0:
        print_success("\nAll dependencies are secure! 🎉")
    else:
        print_error(f"\nFound {total_vulns} vulnerabilities that need attention!")
        print("\nVulnerable files:")
        for file, data in results.items():
            if data.get("status") == "vulnerable":
                print(f"  - {file}: {data['count']} vulnerabilities")


def run_safety_check():
    """Run safety check for additional security scanning"""
    print_header("Running Safety Check")
    
    try:
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Safety check passed!")
        else:
            safety_data = json.loads(result.stdout)
            vuln_count = len(safety_data.get("vulnerabilities", []))
            if vuln_count > 0:
                print_warning(f"Safety found {vuln_count} additional concerns")
                
    except Exception as e:
        print_warning(f"Safety check skipped: {e}")


def main():
    """Main function to run security audit"""
    print_header("Orchestra AI Security Audit Tool")
    print("Checking Python dependencies for known vulnerabilities...\n")
    
    # Check and install tools if needed
    if not check_pip_audit_installed():
        print("Security tools not found. Installing...")
        if not install_security_tools():
            print_error("Failed to install security tools")
            return 1
    
    # Run comprehensive scan
    results, total_vulns = scan_all_requirements()
    
    # Generate report
    generate_report(results, total_vulns)
    
    # Run additional safety check
    run_safety_check()
    
    # Return exit code based on vulnerabilities found
    return 1 if total_vulns > 0 else 0


if __name__ == "__main__":
    sys.exit(main()) 