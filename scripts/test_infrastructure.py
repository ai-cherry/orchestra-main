#!/usr/bin/env python3
"""
Test Infrastructure Setup
========================
Quick tests to verify the AI Orchestra infrastructure is working
"""

import json
import subprocess
import sys
from typing import Any, Dict, List


def run_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"success": True, "output": result.stdout, "error": None}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.stdout, "error": e.stderr}


def test_pulumi_stack():
    """Test Pulumi stack status"""
    print("🔍 Checking Pulumi stack...")

    result = run_command(["pulumi", "stack", "ls", "-C", "infra"])
    if result["success"]:
        print("✅ Pulumi stack is configured")
        print(result["output"])
    else:
        print("❌ Pulumi stack check failed")
        print(result["error"])
        return False

    return True


def test_kubernetes_connection():
    """Test Kubernetes cluster connection"""
    print("\n🔍 Checking Kubernetes connection...")

    result = run_command(["kubectl", "cluster-info"])
    if result["success"]:
        print("✅ Connected to Kubernetes cluster")
    else:
        print("❌ Cannot connect to Kubernetes cluster")
        print("   Run: gcloud container clusters get-credentials <cluster-name>")
        return False

    return True


def test_namespace_resources():
    """Test resources in superagi namespace"""
    print("\n🔍 Checking SuperAGI namespace resources...")

    result = run_command(["kubectl", "get", "all", "-n", "superagi"])
    if result["success"]:
        print("✅ SuperAGI namespace resources:")
        print(result["output"])
    else:
        print("❌ Cannot access SuperAGI namespace")
        return False

    return True


def test_pod_status():
    """Test pod status"""
    print("\n🔍 Checking pod status...")

    result = run_command(["kubectl", "get", "pods", "-n", "superagi", "-o", "json"])

    if result["success"]:
        try:
            pods = json.loads(result["output"])
            running_pods = 0
            failed_pods = []

            for pod in pods.get("items", []):
                name = pod["metadata"]["name"]
                phase = pod["status"]["phase"]

                if phase == "Running":
                    running_pods += 1
                else:
                    failed_pods.append(f"{name} ({phase})")

            print(f"✅ Running pods: {running_pods}")
            if failed_pods:
                print(f"⚠️  Non-running pods: {', '.join(failed_pods)}")

            return running_pods > 0

        except json.JSONDecodeError:
            print("❌ Failed to parse pod status")
            return False
    else:
        print("❌ Cannot get pod status")
        return False


def test_services():
    """Test service endpoints"""
    print("\n🔍 Checking service endpoints...")

    services = ["superagi", "mcp-mongodb", "mcp-weaviate", "dragonfly"]
    available_services = []

    for service in services:
        result = run_command(["kubectl", "get", "svc", service, "-n", "superagi", "-o", "json"])

        if result["success"]:
            try:
                svc = json.loads(result["output"])
                svc_type = svc["spec"]["type"]

                if svc_type == "LoadBalancer":
                    ingress = svc.get("status", {}).get("loadBalancer", {}).get("ingress", [])
                    if ingress:
                        ip = ingress[0].get("ip", "pending")
                        print(f"✅ {service}: {ip}")
                    else:
                        print(f"⏳ {service}: LoadBalancer IP pending")
                else:
                    print(f"✅ {service}: ClusterIP (internal)")

                available_services.append(service)

            except json.JSONDecodeError:
                print(f"⚠️  {service}: Cannot parse service info")
        else:
            print(f"❌ {service}: Not found")

    return len(available_services) > 0


def test_pulumi_outputs():
    """Test Pulumi stack outputs"""
    print("\n🔍 Checking Pulumi outputs...")

    result = run_command(["pulumi", "stack", "output", "--json", "-C", "infra"])

    if result["success"]:
        try:
            outputs = json.loads(result["output"])
            print("✅ Available outputs:")
            for key, value in outputs.items():
                if isinstance(value, dict):
                    print(f"   - {key}: [complex object]")
                else:
                    print(f"   - {key}: {value}")
            return True
        except json.JSONDecodeError:
            print("❌ Failed to parse outputs")
            return False
    else:
        print("❌ Cannot get stack outputs")
        return False


def main():
    """Run all infrastructure tests"""
    print("🚀 AI Orchestra Infrastructure Test Suite")
    print("=" * 50)

    tests = [
        ("Pulumi Stack", test_pulumi_stack),
        ("Kubernetes Connection", test_kubernetes_connection),
        ("Namespace Resources", test_namespace_resources),
        ("Pod Status", test_pod_status),
        ("Services", test_services),
        ("Pulumi Outputs", test_pulumi_outputs),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Infrastructure is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
