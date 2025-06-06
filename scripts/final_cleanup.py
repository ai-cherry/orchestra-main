# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""Final cleanup script to remove GCP references and outdated files."""
    """Handles final cleanup of GCP references and outdated files."""
            r"VULTR_PROJECT_ID",
            r"VULTR_PROJECT_ID",
            r"google-cloud-",
            r"gcp-secret",
            r"secret-manager",
            r"google_cloud_",
            r"firestore",
            r"gcr\.io",
            r"gcp_project_id",
        ]

    def find_outdated_files(self) -> List[Path]:
        """Find files that should be deleted."""
            "GCP_CLEANUP_*.md",
            "cleanup_gcp*.sh",
            "deep_gcp_cleanup.py",
            # Old deployment files
            "cloud_console_guide.md",
            "cloud_shell_bootstrap.sh",
            "cloudbuild*.yaml",
            "deploy_infra_and_images.sh",
            "investigate_403_error.sh",
            "fix_auth_and_investigate.sh",
            "github_actions_wif_setup.txt",
            "github-workflow-wif-template.yml",
            "get_workload_identity_provider.sh",
            "oidc_*.txt",
            "provider_id_info.txt",
            "jwk_info.txt",
            "service_account_access.txt",
            "grant_service_account_access.txt",
            "fixed_attribute_*.txt",
            "fixed_auth_workflow.yml",
            "optimized-github-workflow.yml",
            # Old scripts
            "cleanup_gemini_credentials.sh",
            "cleanup_workspace.sh",
            "delete_all_org_constraints.sh",
            "disable_*.sh",
            "enforce_standard_mode.sh",
            "ensure_standard_mode.sh",
            "exit_restricted_mode.sh",
            "force_standard_mode.py",
            "force_to_standard_mode.sh",
            "prevent_restricted_mode.sh",
            "mode_indicator.sh",
            # Old test files
            "test_mcp_implementation.py",
            "codespaces_*.py",
            "connection_test_config.json",
            "credential_scan_report.json",
            "security-analysis.json",
            # Temporary files
            "pip-unavailable.txt",
            ".bad-reqs.txt",
            ".pip-install.log",
            ".last-pytest.log",
            "mcp_test_results.json",
            # Old documentation
            "COMMIT_FIXES_SUMMARY.md",
            "DEPENDENCY_LOCKDOWN_PLAN.md",
            "deployment_debug_commands.md",
            # Large files
            "get-pip.py",
            "google-cloud-cli-latest-linux-x86_64.tar.gz",
            # Old configs
            "phi_config.yaml",
            "phidata_*.yaml",
            "component*.json",
            "component*.csv",
        ]

        files_to_delete = []
        for pattern in outdated_patterns:
            files_to_delete.extend(self.root_dir.glob(pattern))
            files_to_delete.extend(self.root_dir.glob(f"**/{pattern}"))

        return list(set(files_to_delete))

    def find_files_with_gcp_references(self) -> List[Path]:
        """Find files that contain GCP references."""
        skip_dirs = {".git", ".mypy_cache", "venv", "__pycache__", "node_modules"}

        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file() and not any(skip in str(file_path) for skip in skip_dirs):
                try:

                    pass
                    content = file_path.read_text(encoding="utf-8")
                    for pattern in self.gcp_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            files_with_gcp.append(file_path)
                            break
                except Exception:

                    pass
                    pass

        return files_with_gcp

    def update_file_content(self, file_path: Path) -> bool:
        """Update file to remove GCP references."""
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Replace GCP references
            replacements = {
                r"VULTR_PROJECT_ID": "PROJECT_ID",
                r"VULTR_PROJECT_ID": "PROJECT_ID",
                r"google-cloud-secret-manager": "# google-cloud-secret-manager (removed)",
                r"google-cloud-firestore": "# google-cloud-firestore (removed)",
                r"google-cloud-storage": "# google-cloud-storage (removed)",
                r"gcr\.io/\$\{\{[^}]+\}\}": "registry.digitalocean.com/${DO_REGISTRY}",
                r"gcp_project_id": "project_id",
            }

            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

            if content != original_content:
                file_path.write_text(content)
                return True
            return False
        except Exception:

            pass
            print(f"Error updating {file_path}: {e}")
            return False

    def run(self):
        """Run the final cleanup."""
        print("🧹 Starting final cleanup...\n")

        # Find outdated files
        print("📋 Finding outdated files...")
        outdated_files = self.find_outdated_files()

        if outdated_files:
            print(f"\nFound {len(outdated_files)} files to delete:")
            for f in sorted(outdated_files):
                print(f"  - {f.relative_to(self.root_dir)}")

            response = input("\nDelete these files? (y/N): ")
            if response.lower() == "y":
                for f in outdated_files:
                    try:

                        pass
                        f.unlink()
                        print(f"  ✓ Deleted {f.relative_to(self.root_dir)}")
                    except Exception:

                        pass
                        print(f"  ✗ Error deleting {f}: {e}")

        # Find files with GCP references
        print("\n📋 Finding files with GCP references...")
        gcp_files = self.find_files_with_gcp_references()

        # Filter out files we shouldn't modify
        exclude_patterns = [
            "FINAL_INFRASTRUCTURE_UPDATE.md",
            "SECRET_MANAGEMENT_STATUS.md",
            "INFRASTRUCTURE_STATUS.md",
            "scripts/migrate_all_secrets_to_pulumi.py",
            "scripts/final_cleanup.py",
            ".git/",
        ]

        gcp_files = [f for f in gcp_files if not any(pattern in str(f) for pattern in exclude_patterns)]

        if gcp_files:
            print(f"\nFound {len(gcp_files)} files with GCP references:")
            for f in sorted(gcp_files)[:20]:  # Show first 20
                print(f"  - {f.relative_to(self.root_dir)}")
            if len(gcp_files) > 20:
                print(f"  ... and {len(gcp_files) - 20} more")

            response = input("\nUpdate these files to remove GCP references? (y/N): ")
            if response.lower() == "y":
                updated = 0
                for f in gcp_files:
                    if self.update_file_content(f):
                        updated += 1
                        print(f"  ✓ Updated {f.relative_to(self.root_dir)}")
                print(f"\n✅ Updated {updated} files")

        # Update specific configuration files
        print("\n📋 Updating configuration files...")
        self.update_config_files()

        print("\n✅ Cleanup complete!")
        print("\nNext steps:")
        print("1. Review the changes: git status")
        print(
            "2. Commit the cleanup: git add -A && git commit -m 'chore: Final cleanup - remove GCP references and outdated files'"
        )
        print("3. Push to remote: git push origin main")

    def update_config_files(self):
        """Update specific configuration files."""
            "docker-compose.yml": [
                ("VULTR_PROJECT_ID:", "# VULTR_PROJECT_ID: (removed)"),
                ("VULTR_PROJECT_ID:", "# VULTR_PROJECT_ID: (removed)"),
            ],
            # Update .github/workflows/main.yml
            ".github/workflows/main.yml": [
                (
                    "pip install google-cloud-secret-manager",
                    "# pip install google-cloud-secret-manager (removed)",
                ),
            ],
            # Update requirements files
            "requirements/base.txt": [
                ("google-cloud-", "# google-cloud- (removed)"),
            ],
        }

        for file_path, replacements in updates.items():
            full_path = self.root_dir / file_path
            if full_path.exists():
                try:

                    pass
                    content = full_path.read_text()
                    for old, new in replacements:
                        content = content.replace(old, new)
                    full_path.write_text(content)
                    print(f"  ✓ Updated {file_path}")
                except Exception:

                    pass
                    print(f"  ✗ Error updating {file_path}: {e}")

def main():
    """Main entry point."""
if __name__ == "__main__":
    main()
