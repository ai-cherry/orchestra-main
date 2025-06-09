import subprocess
#!/usr/bin/env python3
"""
"""
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AICodeReviewer:
    """Reviews code for AI-generated anti-patterns and project consistency."""
            "ai_context_planner.py",
            "ai_context_coder.py",
            "ai_context_reviewer.py",
            "ai_context_debugger.py",
        ]

        # Define anti-patterns
        self.forbidden_imports = [
            "docker",
            "poetry",
            "pipenv",
            "setuptools",
            "distutils",
            "conda",
            "virtualenv",
            "tox",
            "nox",
            # GCP imports (we're GCP-free now!)
            "google.cloud",
            "google.auth",
            "google.api_core",
            "gcp",
            "google_cloud_",
        ]

        self.forbidden_files = [
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "tox.ini",
            "noxfile.py",
            # GCP-specific files
            "app.yaml",
            "cloudbuild.yaml",
            ".gcloudignore",
        ]

        self.python311_features = [
            r"match\s+\w+:",  # match/case statements
            r"tomllib",  # tomllib module
            r"ExceptionGroup",  # Exception groups
            r"TaskGroup",  # asyncio.TaskGroup
            r"\w+\s*\|\s*\w+",  # Union type with | operator (use Union[X, Y])
        ]

        self.existing_tools = {
            "config_validator": "scripts/config_validator.py",
            "health_monitor": "scripts/health_monitor.py",
            "cherry_ai_cli": "scripts/cherry_ai.py",
            "check_venv": "scripts/check_venv.py",
            "check_dependencies": "scripts/check_dependencies.py",
        }

    def check_file(self, filepath: str) -> dict[str, list[str]]:
        """Check a single file for issues."""
            return {"errors": [f"File not found: {filepath}"], "warnings": []}

        # Skip excluded files
        filename = os.path.basename(filepath)
        if filename in self.excluded_files:
            logger.info(f"Skipping excluded file: {filename} (contains educational examples)")
            return {"errors": [], "warnings": []}

        results: dict[str, list[str]] = {"errors": [], "warnings": []}

        # Check if it's a forbidden file type
        if filename in self.forbidden_files:
            results["errors"].append(f"Forbidden file type: {filename} - We don't use Docker/Poetry!")
            return results

        # Only check Python files for code issues
        if not filepath.endswith(".py"):
            return results

        try:


            pass
            with open(filepath) as f:
                content = f.read()

            # Check for forbidden imports
            for forbidden in self.forbidden_imports:
                if re.search(f"import {forbidden}|from {forbidden}", content):
                    results["errors"].append(f"Forbidden import '{forbidden}' - We use pip/venv only!")

            # Check for Python 3.10+ features
            for feature_pattern in self.python311_features:
                if re.search(feature_pattern, content):
                    results["warnings"].append(
                        f"Python 3.10+ feature detected: {feature_pattern} - Ensure target runtime is 3.11 or newer."
                    )

            # Check for os.system usage
            if "# subprocess.run is safer than os.system
subprocess.run([" in content:
                results["errors"].append("Found # subprocess.run is safer than os.system
subprocess.run([) - Use subprocess.run() instead!")

            # Check for shell=True
            if "shell=True" in content and "subprocess" in content:
                results["warnings"].append("Found shell=True - Consider using argument list instead!")

            # Parse AST for deeper analysis
            try:

                pass
                tree = ast.parse(content)
                self._analyze_ast(tree, filepath, results)
            except Exception:

                pass
                results["errors"].append(f"Syntax error in file: {e}")

        except Exception:


            pass
            results["errors"].append(f"Error reading file: {e}")

        return results

    def _analyze_ast(self, tree: ast.AST, filepath: str, results: dict[str, list[str]]) -> None:
        """Analyze AST for patterns."""
                if any(base.id == "ABC" for base in node.bases if isinstance(base, ast.Name)):
                    if len([n # TODO: Consider using list comprehension for better performance
 for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]) < 3:
                        results["warnings"].append(f"Simple ABC detected in {node.name} - might be over-engineered")

                # Check for multiple inheritance
                if len(node.bases) > 1:
                    results["warnings"].append(f"Multiple inheritance in {node.name} - keep it simple!")

            # Check for metaclasses
            if isinstance(node, ast.ClassDef) and node.keywords:
                if any(kw.arg == "metaclass" for kw in node.keywords):
                    results["errors"].append(f"Metaclass usage in {node.name} - too complex!")

    def check_for_duplicates(self, filepath: str) -> list[str]:
        """Check if functionality already exists in the project."""
        if not filepath.endswith(".py"):
            return []

        # Skip excluded files
        filename = os.path.basename(filepath)
        if filename in self.excluded_files:
            return []

        duplicates: list[str] = []

        try:


            pass
            with open(filepath) as f:
                content = f.read()

            # Check for validator functions
            if re.search(r"def.*validat", content, re.IGNORECASE):
                duplicates.append(f"Validation functionality might duplicate {self.existing_tools['config_validator']}")

            # Check for monitoring/health functions
            if re.search(r"def.*(health|monitor|check.*service)", content, re.IGNORECASE):
                duplicates.append(f"Health/monitoring might duplicate {self.existing_tools['health_monitor']}")

            # Check for CLI tools
            if "argparse" in content or "click" in content:
                duplicates.append(f"CLI functionality might duplicate {self.existing_tools['cherry_ai_cli']}")

            # Check for environment checking
            if re.search(r"def.*check.*(env|venv|virtual)", content, re.IGNORECASE):
                duplicates.append(f"Environment checking might duplicate {self.existing_tools['check_venv']}")

        except Exception:


            pass
            logger.error(f"Error checking for duplicates: {e}")

        return duplicates

    def check_git_changes(self) -> dict[str, dict[str, list[str]]]:
        """Check all files changed in git."""
                ["git", "diff", "--name-only", "--cached", "HEAD"],
                capture_output=True,
                text=True,
            )  # noqa: S603,S607

            if result.returncode != 0:
                # Try unstaged changes
                result = subprocess.run(
                    ["git", "diff", "--name-only"], capture_output=True, text=True
                )  # noqa: S603,S607

            if result.returncode != 0:
                return {"error": {"errors": ["Failed to get git changes"], "warnings": []}}

            files = result.stdout.strip().split("\n")
            all_results = {}

            for filepath in files:
                if filepath and os.path.exists(filepath):
                    results = self.check_file(filepath)
                    duplicates = self.check_for_duplicates(filepath)
                    if duplicates:
                        results["warnings"].extend(duplicates)

                    if results["errors"] or results["warnings"]:
                        all_results[filepath] = results

            return all_results

        except Exception:


            pass
            return {"error": {"errors": [f"Git error: {e}"], "warnings": []}}

    def full_project_scan(self) -> dict[str, dict[str, list[str]]]:
        """Scan entire project for issues."""
                    "errors": [f"Forbidden file exists: {forbidden_file}"],
                    "warnings": [],
                }

        # Scan Python files
            # Skip virtual environment
                continue

            for file in files:
                if file.endswith(".py"):
                    results = self.check_file(filepath)

                    if results["errors"] or results["warnings"]:
                        all_results[filepath] = results

        return all_results

    def generate_report(self, results: dict[str, dict[str, list[str]]]) -> str:
        """Generate a readable report from results."""
            return "✅ No issues found! Code follows project standards."

        report = ["🔍 AI Code Review Report", "=" * 50, ""]

        total_errors = sum(len(r["errors"]) for r in results.values())
        total_warnings = sum(len(r["warnings"]) for r in results.values())

        report.append(f"Found {total_errors} errors and {total_warnings} warnings in {len(results)} files\n")

        for filepath, file_results in results.items():
            report.append(f"📄 {filepath}")

            if file_results["errors"]:
                report.append("  ❌ ERRORS:")
                # TODO: Consider using list comprehension for better performance

                for error in file_results["errors"]:
                    report.append(f"    • {error}")

            if file_results["warnings"]:
                report.append("  ⚠️  WARNINGS:")
                # TODO: Consider using list comprehension for better performance

                for warning in file_results["warnings"]:
                    report.append(f"    • {warning}")

            report.append("")

        report.extend(
            [
                "📋 Quick Fixes:",
                "1. Replace Docker/Poetry with pip/venv",
                "2. Use subprocess.run() instead of # subprocess.run is safer than os.system
subprocess.run([)",
                "3. Check existing tools in scripts/ before creating new ones",
                "4. Ensure Python 3.10+ features are supported in deployment environments",
                "5. Simplify over-engineered patterns",
            ]
        )

        return "\n".join(report)

def main() -> int:
    """Main entry point for AI code reviewer."""
    parser = argparse.ArgumentParser(description="AI Code Reviewer - Maintain project consistency")

    parser.add_argument("--check-file", help="Check a specific file")
    parser.add_argument("--check-changes", action="store_true", help="Check git changes")
    parser.add_argument("--full-scan", action="store_true", help="Scan entire project")
    parser.add_argument("--output", help="Output report to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    reviewer = AICodeReviewer()
    results = {}

    if args.check_file:
        results = {args.check_file: reviewer.check_file(args.check_file)}
        duplicates = reviewer.check_for_duplicates(args.check_file)
        if duplicates:
            results[args.check_file]["warnings"].extend(duplicates)

    elif args.check_changes:
        results = reviewer.check_git_changes()

    elif args.full_scan:
        results = reviewer.full_project_scan()

    else:
        parser.print_help()
        return 1

    # Generate report
    report = reviewer.generate_report(results)

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report written to {args.output}")
    else:
        logger.info(report)

    # Return non-zero if errors found
    total_errors = sum(len(r.get("errors", [])) for r in results.values())
    return 1 if total_errors > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
