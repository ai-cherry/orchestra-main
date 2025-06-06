#!/usr/bin/env python3
"""
"""
    """Pattern for detecting hardcoded values."""
        name="Lambda API Key",
        pattern=re.compile(r'["\'][A-Z0-9]{30,60}["\']'), # Generic strong API key pattern
        env_var="LAMBDA_API_KEY",
        description="Potential Lambda API Key or similar secret.",
        file_patterns=[r"\.sh$", r"\.ya?ml$", r"\.py$"],
    ),
    HardcodedPattern(
        name="Generic Project ID",
        pattern=re.compile(r'["\'][a-z0-9-]+-[a-z0-9]+(?:-[a-z0-9]+)?["\']'),
        env_var="PROJECT_ID", # Generic, user can map to LAMBDA_PROJECT_ID
        description="Potential cloud project ID. Verify if it relates to lambda.",
        file_patterns=[r"\.sh$", r"\.ya?ml$", r"\.py$"],
    ),
    HardcodedPattern(
        name="Generic Region/Zone",
        pattern=re.compile(r'["\'][a-z]+(?:-[a-z]+)-\d[a-z]?["\']'), # e.g., fra-1, ams-1a
        env_var="LAMBDA_REGION", # Or Lambda_ZONE
        description="Potential cloud region/zone. Verify if it relates to lambda.",
        file_patterns=[r"\.sh$", r"\.ya?ml$", r"\.py$"],
    ),
    HardcodedPattern(
        name="Lambda Resource Name",
        pattern=re.compile(r'["\']Lambda-[a-zA-Z0-9_.-]+["\']'),
        env_var="Lambda_RESOURCE_NAME_VAR", # Placeholder for specific Lambda resource names
        description="Potential hardcoded Lambda-specific resource name.",
        file_patterns=[r"\.sh$", r"\.ya?ml$", r"\.py$"],
    ),
    HardcodedPattern(
        name="IP Address",
        pattern=re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        env_var="SERVER_IP_ADDRESS",
        description="Potential hardcoded IP address. Should be configurable.",
        file_patterns=[r"\.sh$", r"\.ya?ml$", r"\.py$", r"\.conf$", r"nginx\.conf$"],
        exclude_patterns=[r"127\.0\.0\.1", r"0\.0\.0\.0", r"localhost"], # Exclude common local IPs
    ),
    HardcodedPattern(
        name="Domain Name",
        pattern=re.compile(r'["\'][a-zA-Z0-9.-]+\.(?:com|org|net|io|ai|dev)["\']'),
        env_var="DOMAIN_NAME",
        description="Potential hardcoded domain name.",
        file_patterns=[r"\.py$", r"\.ya?ml$", r"\.conf$", r"nginx\.conf$"],
        exclude_patterns=[r"localhost", r"example\.com"], # Exclude common examples
    ),
]

def should_scan_file(file_path: Path, pattern: HardcodedPattern) -> bool:
    """Check if a file should be scanned based on patterns."""
    if file_path.name.startswith(".env"):
        return False

    # Skip files that don't match any include pattern
    if not any(re.search(p, str(file_path)) for p in pattern.file_patterns):
        return False

    # Skip files that match any exclude pattern
    if pattern.exclude_patterns and any(re.search(p, str(file_path)) for p in pattern.exclude_patterns):
        return False

    return True

def scan_file(file_path: Path, pattern: HardcodedPattern) -> List[Tuple[int, str, str]]:
    """
    """
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                for match in pattern.pattern.finditer(line):
                    results.append((i, line.strip(), match.group(0)))
    except Exception:

        pass
        # Skip binary files
        pass

    return results

def generate_fix(file_path: Path, pattern: HardcodedPattern, line: str, match: str) -> str:
    """
    """
    if file_path.suffix == ".sh":
        # For shell scripts
        return line.replace(match, f"${{{pattern.env_var}}}")
    elif file_path.suffix in (".yml", ".yaml"):
        # For YAML files
        return line.replace(match, f"${{{{ env.{pattern.env_var} }}}}")
    elif file_path.suffix == ".py":
        # For Python files
        return line.replace(match, f'os.environ.get("{pattern.env_var}", {match})')
    else:
        # Default
        return line.replace(match, f"${{{pattern.env_var}}}")

def scan_directory(
    directory: Path, fix: bool = False
) -> Dict[Path, Dict[str, List[Tuple[int, str, str, Optional[str]]]]]:
    """
    """
    """
    """
    print(f"Found {total_matches} hardcoded values in {total_files} files:\n")

    for file_path, file_results in sorted(results.items()):
        print(f"\n{file_path}:")
        for pattern_name, matches in file_results.items():
            print(f"  {pattern_name}:")
            for line_num, line, match, fix in matches:
                print(f"    Line {line_num}: {line}")
                if fix:
                    print(f"    Suggested fix: {fix}")
                print()

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Scan for hardcoded values in AI cherry_ai codebase")
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to scan (default: current directory)",
    )
    parser.add_argument("--fix", action="store_true", help="Generate suggested fixes")
    args = parser.parse_args()

    directory = Path(args.path)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)

    print(f"Scanning {directory} for hardcoded values...")
    results = scan_directory(directory, args.fix)
    print_results(results)

if __name__ == "__main__":
    main()
