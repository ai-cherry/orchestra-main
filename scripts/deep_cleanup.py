#!/usr/bin/env python3
"""Deep cleanup script to analyze and remove files that don't fit current structure."""

import re
from pathlib import Path
from typing import List, Dict
import json


class DeepCleanup:
    """Performs deep analysis and cleanup of GCP references."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.gcp_patterns = [
            r"GCP_PROJECT_ID",
            r"GOOGLE_CLOUD_PROJECT",
            r"google-cloud-",
            r"gcp-secret",
            r"secret-manager",
            r"google_cloud_",
            r"firestore",
            r"gcr\.io",
            r"gcp_project_id",
        ]

        # Files/directories that should be kept even with GCP references
        self.keep_patterns = [
            "FINAL_INFRASTRUCTURE_UPDATE.md",
            "SECRET_MANAGEMENT_STATUS.md",
            "INFRASTRUCTURE_STATUS.md",
            "CLEANUP_SUMMARY.md",
            "scripts/migrate_all_secrets_to_pulumi.py",
            "scripts/final_cleanup.py",
            "scripts/deep_cleanup.py",
            ".git/",
            "venv/",
            ".mypy_cache/",
            "__pycache__/",
            "node_modules/",
        ]

        # Categories of files to analyze
        self.categories = {
            "deployment": ["deploy", "build", "ci", "cd", "workflow", "pipeline"],
            "gcp_specific": [
                "gcp",
                "google",
                "gcr",
                "gke",
                "firestore",
                "bigquery",
                "pubsub",
            ],
            "old_config": ["phi_", "phidata", "gemini", "vertex", "workstation"],
            "test_files": ["test_", "_test.py", "spec.", "mock"],
            "documentation": [".md", "README", "GUIDE", "docs/"],
            "scripts": [".sh", ".py", "script"],
            "config": [".yaml", ".yml", ".json", "config"],
        }

    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """Analyze a file for GCP references and categorize it."""
        analysis = {
            "path": file_path,
            "size": file_path.stat().st_size,
            "gcp_references": [],
            "categories": [],
            "recommendation": "keep",
            "reason": "",
        }

        # Categorize file
        rel_path = str(file_path.relative_to(self.root_dir))
        for category, patterns in self.categories.items():
            if any(pattern in rel_path.lower() for pattern in patterns):
                analysis["categories"].append(category)

        # Find GCP references
        try:
            content = file_path.read_text(encoding="utf-8")
            for pattern in self.gcp_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis["gcp_references"].extend(matches)
        except Exception:
            analysis["reason"] = "Could not read file"
            return analysis

        # Make recommendation
        analysis["recommendation"] = self.recommend_action(rel_path, analysis)

        return analysis

    def recommend_action(self, rel_path: str, analysis: Dict) -> str:
        """Recommend whether to keep, update, or delete a file."""

        # Always keep certain files
        if any(pattern in rel_path for pattern in self.keep_patterns):
            analysis["reason"] = "Protected file"
            return "keep"

        # Delete old GCP-specific files
        if "gcp_specific" in analysis["categories"]:
            if any(
                x in rel_path.lower()
                for x in ["gemini", "vertex", "workstation", "cloudbuild"]
            ):
                analysis["reason"] = "GCP-specific tool/service"
                return "delete"

        # Delete old deployment files
        if "deployment" in analysis["categories"]:
            if any(
                x in rel_path.lower() for x in ["gcp", "google", "cloud-run", "gke"]
            ):
                analysis["reason"] = "GCP deployment file"
                return "delete"

        # Delete old config files
        if "old_config" in analysis["categories"]:
            if any(x in rel_path.lower() for x in ["phi_", "phidata", "gemini"]):
                analysis["reason"] = "Old configuration system"
                return "delete"

        # Delete specific problematic files
        delete_patterns = [
            "codespaces",
            "cloud_shell",
            "cloudbuild",
            "workstation",
            "wif_",
            "oidc_",
            "service_account",
            "gcp_auth",
            "google_auth",
            "firestore",
            "bigquery",
            "pubsub",
            "cloud_run",
            "gcr.io",
            "artifact_registry",
        ]

        if any(pattern in rel_path.lower() for pattern in delete_patterns):
            analysis["reason"] = "Contains GCP-specific pattern"
            return "delete"

        # Keep but mark for update
        if len(analysis["gcp_references"]) > 5:
            analysis["reason"] = "Many GCP references - needs update"
            return "update"

        # Default to keep
        analysis["reason"] = "Minor references only"
        return "keep"

    def find_all_gcp_files(self) -> List[Path]:
        """Find all files with GCP references."""
        files_with_gcp = []
        skip_dirs = {".git", ".mypy_cache", "venv", "__pycache__", "node_modules"}

        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file() and not any(
                skip in str(file_path) for skip in skip_dirs
            ):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for pattern in self.gcp_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            files_with_gcp.append(file_path)
                            break
                except Exception:
                    pass

        return files_with_gcp

    def run(self):
        """Run the deep cleanup analysis."""
        print("🔍 Starting deep cleanup analysis...\n")

        # Find all files with GCP references
        print("📋 Finding all files with GCP references...")
        gcp_files = self.find_all_gcp_files()
        print(f"Found {len(gcp_files)} files with GCP references\n")

        # Analyze each file
        print("🔬 Analyzing files...")
        results = {"delete": [], "update": [], "keep": []}

        for file_path in gcp_files:
            analysis = self.analyze_file(file_path)
            results[analysis["recommendation"]].append(analysis)

        # Show summary
        print("\n📊 Analysis Summary:")
        print(f"  - Files to DELETE: {len(results['delete'])}")
        print(f"  - Files to UPDATE: {len(results['update'])}")
        print(f"  - Files to KEEP: {len(results['keep'])}")

        # Show files to delete
        if results["delete"]:
            print("\n🗑️  Files recommended for DELETION:")
            for item in sorted(results["delete"], key=lambda x: str(x["path"])):
                rel_path = item["path"].relative_to(self.root_dir)
                print(f"  - {rel_path}")
                print(f"    Reason: {item['reason']}")
                print(f"    Categories: {', '.join(item['categories'])}")

        # Show files to update
        if results["update"]:
            print("\n✏️  Files recommended for UPDATE:")
            for item in sorted(results["update"], key=lambda x: str(x["path"]))[:10]:
                rel_path = item["path"].relative_to(self.root_dir)
                print(f"  - {rel_path}")
                print(f"    GCP refs: {len(item['gcp_references'])}")
            if len(results["update"]) > 10:
                print(f"  ... and {len(results['update']) - 10} more")

        # Ask for confirmation
        if results["delete"]:
            print(f"\n⚠️  Ready to delete {len(results['delete'])} files")
            response = input("Proceed with deletion? (y/N): ")
            if response.lower() == "y":
                deleted = 0
                for item in results["delete"]:
                    try:
                        item["path"].unlink()
                        print(f"  ✓ Deleted {item['path'].relative_to(self.root_dir)}")
                        deleted += 1
                    except Exception as e:
                        print(f"  ✗ Error deleting {item['path']}: {e}")
                print(f"\n✅ Deleted {deleted} files")

        # Save analysis report
        report_path = self.root_dir / "deep_cleanup_report.json"
        report_data = {
            "total_files": len(gcp_files),
            "delete": len(results["delete"]),
            "update": len(results["update"]),
            "keep": len(results["keep"]),
            "files": {
                "delete": [
                    str(x["path"].relative_to(self.root_dir)) for x in results["delete"]
                ],
                "update": [
                    str(x["path"].relative_to(self.root_dir)) for x in results["update"]
                ][:20],
            },
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Analysis report saved to: {report_path}")
        print("\nNext steps:")
        print("1. Review the changes: git status")
        print(
            "2. Commit if satisfied: git add -A && git commit -m 'chore: Deep cleanup of GCP references'"
        )
        print(
            "3. For remaining files needing updates, use the report to guide manual updates"
        )


def main():
    """Main entry point."""
    cleanup = DeepCleanup()
    cleanup.run()


if __name__ == "__main__":
    main()
