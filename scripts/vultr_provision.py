#!/usr/bin/env python3
"""Provision a Vultr instance and attach block storage.

Requires ``VULTR_API_KEY`` environment variable.

Usage:
    python scripts/vultr_provision.py --region ewr --plan vc2-1c-2gb --os 215 \
        --label orchestra-ai --ssh-key <key_id> --volume <volume_id>
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

import requests

API_BASE = "https://api.vultr.com/v2"

def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

def create_instance(
    api_key: str, region: str, plan: str, os_id: str, label: str, ssh_key: Optional[str]
) -> tuple[str, str]:
    payload = {"region": region, "plan": plan, "os_id": os_id, "label": label}
    if ssh_key:
        payload["sshkey_id"] = ssh_key
    resp = requests.post(f"{API_BASE}/instances", json=payload, headers=_headers(api_key), timeout=30)
    resp.raise_for_status()
    data = resp.json()["instance"]
    return data["id"], data["main_ip"]

def attach_volume(api_key: str, instance_id: str, volume_id: str) -> None:
    payload = {"instance_id": instance_id}
    resp = requests.post(f"{API_BASE}/volumes/{volume_id}/attach", json=payload, headers=_headers(api_key), timeout=30)
    resp.raise_for_status()

def main() -> None:
    parser = argparse.ArgumentParser(description="Provision Vultr server")
    parser.add_argument("--region", default="ewr", help="Vultr region ID (default: ewr)")
    parser.add_argument("--plan", default="vc2-1c-2gb", help="Vultr plan ID")
    parser.add_argument("--os", dest="os_id", default="215", help="OS ID (default Ubuntu 22.04)")
    parser.add_argument("--label", default="orchestra-ai", help="Instance label")
    parser.add_argument("--ssh-key", help="SSH key ID")
    parser.add_argument("--volume", help="Existing block storage volume ID")
    args = parser.parse_args()

    api_key = os.environ.get("VULTR_API_KEY")
    if not api_key:
        sys.exit("VULTR_API_KEY environment variable not set")

    instance_id, ip = create_instance(api_key, args.region, args.plan, args.os_id, args.label, args.ssh_key)
    print(f"Created instance {instance_id} with IP {ip}")

    if args.volume:
        attach_volume(api_key, instance_id, args.volume)
        print(f"Attached volume {args.volume} to instance {instance_id}")

if __name__ == "__main__":
    main()
