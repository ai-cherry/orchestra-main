#!/usr/bin/env python3
# validate_best_practices.py - Assesses GCP best practices

import sys
import json
import argparse
import subprocess
from pathlib import Path


def check_iam_practices(project_id):
    """Check IAM best practices"""
    try:
        # List service accounts
        result = subprocess.run(
            [
                "gcloud",
                "iam",
                "service-accounts",
                "list",
                f"--project={project_id}",
                "--format=json",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            service_accounts = (
                json.loads(result.stdout) if result.stdout.strip() else []
            )

            # Check for overly permissive accounts
            recommendations = []
            for sa in service_accounts:
                email = sa.get("email", "")
                if "compute@developer" in email or "editor" in email:
                    recommendations.append(
                        f"Service account {email} may have overly broad permissions"
                    )

            return True, {
                "service_accounts": len(service_accounts),
                "recommendations": recommendations,
            }
        else:
            return False, f"Error listing service accounts: {result.stderr}"
    except Exception as e:
        return False, f"Error checking IAM practices: {str(e)}"


def check_docker_practices():
    """Check Docker best practices"""
    try:
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            return False, "Dockerfile not found"

        content = dockerfile.read_text()

        recommendations = []

        # Check for best practices
        if "COPY --from=builder" not in content and "multi-stage" not in content:
            recommendations.append(
                "Consider using multi-stage builds to reduce image size"
            )

        if (
            "apt-get update && apt-get install" in content
            and "apt-get clean" not in content
        ):
            recommendations.append(
                "Add 'apt-get clean' after installations to reduce image size"
            )

        if "USER root" in content or "USER 0" in content:
            recommendations.append("Avoid running containers as root when possible")

        if "HEALTHCHECK" not in content:
            recommendations.append("Consider adding HEALTHCHECK instruction")

        return True, {"dockerfile_exists": True, "recommendations": recommendations}
    except Exception as e:
        return False, f"Error checking Docker practices: {str(e)}"


def check_monitoring_practices(project_id):
    """Check monitoring best practices"""
    try:
        # Check for custom metrics
        result = subprocess.run(
            [
                "gcloud",
                "monitoring",
                "metrics",
                "descriptors",
                "list",
                f"--project={project_id}",
                '--filter=metric.type=starts_with("custom.googleapis.com")',
                "--format=json",
            ],
            capture_output=True,
            text=True,
        )

        recommendations = []

        if result.returncode == 0:
            metrics = json.loads(result.stdout) if result.stdout.strip() else []

            if not metrics:
                recommendations.append(
                    "No custom metrics found. Consider implementing custom metrics for application-specific monitoring"
                )

            # Check for alerting policies
            alert_result = subprocess.run(
                [
                    "gcloud",
                    "monitoring",
                    "policies",
                    "list",
                    f"--project={project_id}",
                    "--format=json",
                ],
                capture_output=True,
                text=True,
            )

            if alert_result.returncode == 0:
                policies = (
                    json.loads(alert_result.stdout)
                    if alert_result.stdout.strip()
                    else []
                )

                if not policies:
                    recommendations.append(
                        "No alerting policies found. Consider setting up alerts for critical metrics"
                    )

            return True, {
                "custom_metrics": len(metrics),
                "alert_policies": len(policies)
                if "policies" in locals()
                else "unknown",
                "recommendations": recommendations,
            }
        else:
            return False, f"Error checking monitoring practices: {result.stderr}"
    except Exception as e:
        return False, f"Error checking monitoring practices: {str(e)}"


def check_terraform_usage():
    """Check for Terraform usage as infrastructure-as-code"""
    terraform_dirs = ["terraform", "infra", "tf"]
    terraform_files = []

    for dir_name in terraform_dirs:
        if Path(dir_name).is_dir():
            terraform_files.extend(list(Path(dir_name).glob("**/*.tf")))

    # Also check for any .tf files in project root
    terraform_files.extend(list(Path(".").glob("*.tf")))

    if terraform_files:
        return True, f"Found {len(terraform_files)} Terraform files in the project"
    else:
        return False, "No Terraform files found. Consider using infrastructure-as-code"


def check_security_practices():
    """Check for security best practices"""
    recommendations = []

    # Check for .env files that might contain secrets
    env_files = list(Path(".").glob("**/.env"))
    if env_files:
        recommendations.append(
            f"Found {len(env_files)} .env files. Ensure these are not committed to source control and use Secret Manager instead"
        )

    # Check for potential hardcoded secrets in Python files
    secret_patterns = ["api_key", "apikey", "secret", "password", "token"]
    potential_secret_files = []

    for pattern in secret_patterns:
        try:
            result = subprocess.run(
                ["grep", "-l", "-i", pattern, "--include=*.py", "-r", "."],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout:
                files = result.stdout.strip().split("\n")
                potential_secret_files.extend(files)
        except Exception:
            pass

    if potential_secret_files:
        recommendations.append(
            f"Found {len(set(potential_secret_files))} Python files with potential hardcoded secrets. Use Secret Manager instead"
        )

    # Check for Secret Manager usage
    has_secret_manager = False
    try:
        result = subprocess.run(
            ["grep", "-l", "secretmanager", "--include=*.py", "-r", "."],
            capture_output=True,
            text=True,
        )
        has_secret_manager = result.returncode == 0 and result.stdout
    except Exception:
        pass

    if not has_secret_manager:
        recommendations.append(
            "No Secret Manager usage detected. Consider using GCP Secret Manager for sensitive information"
        )

    return True, recommendations


def main():
    parser = argparse.ArgumentParser(description="Validate GCP best practices")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="GCP Location")
    args = parser.parse_args()

    print("### GCP Best Practices Assessment")

    print("#### IAM & Security Best Practices")
    iam_ok, iam_results = check_iam_practices(args.project)
    if iam_ok and isinstance(iam_results, dict):
        print(f"* Service accounts found: {iam_results['service_accounts']}")
        if iam_results["recommendations"]:
            print("* Recommendations:")
            for rec in iam_results["recommendations"]:
                print(f"  * {rec}")
        else:
            print("* No IAM recommendations identified")
    else:
        print(f"* Error checking IAM practices: {iam_results}")

    print("\n#### Docker & Containerization Best Practices")
    docker_ok, docker_results = check_docker_practices()
    if docker_ok and isinstance(docker_results, dict):
        if docker_results["recommendations"]:
            print("* Recommendations:")
            for rec in docker_results["recommendations"]:
                print(f"  * {rec}")
        else:
            print("* No Docker recommendations identified")
    else:
        print(f"* Error checking Docker practices: {docker_results}")

    print("\n#### Monitoring & Observability Best Practices")
    monitoring_ok, monitoring_results = check_monitoring_practices(args.project)
    if monitoring_ok and isinstance(monitoring_results, dict):
        print(f"* Custom metrics found: {monitoring_results['custom_metrics']}")
        print(f"* Alert policies found: {monitoring_results['alert_policies']}")
        if monitoring_results["recommendations"]:
            print("* Recommendations:")
            for rec in monitoring_results["recommendations"]:
                print(f"  * {rec}")
        else:
            print("* No monitoring recommendations identified")
    else:
        print(f"* Error checking monitoring practices: {monitoring_results}")

    print("\n#### Infrastructure-as-Code Practices")
    terraform_ok, terraform_msg = check_terraform_usage()
    print(f"* Terraform usage: {'✅' if terraform_ok else '❌'}")
    print(f"  * {terraform_msg}")

    print("\n#### Security Best Practices")
    security_ok, security_recommendations = check_security_practices()
    if security_recommendations:
        print("* Recommendations:")
        for rec in security_recommendations:
            print(f"  * {rec}")
    else:
        print("* No security recommendations identified")

    print("\n#### General GCP Best Practices")
    print("* Recommendations:")
    print(
        "  * Use Workload Identity Federation instead of service account keys when possible"
    )
    print("  * Implement least privilege access for all service accounts")
    print("  * Set up budget alerts to prevent unexpected billing charges")
    print("  * Use terraform or infrastructure-as-code for managing GCP resources")
    print("  * Implement CI/CD pipelines for all application deployments")
    print("  * Use Secret Manager for all sensitive credentials")
    print("  * Consider implementing VPC Service Controls for sensitive projects")
    print("  * Enable Cloud Audit Logs for all important resources")
    print("  * Use Cloud Armor for web application firewall protection")
    print("  * Implement regular backups and disaster recovery testing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
