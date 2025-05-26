"""
Backup Manager for AI Orchestra
===============================
Manages automated backups for DragonflyDB and Firestore
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import redis
from google.cloud import firestore, storage
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backups for all data stores"""

    def __init__(
        self, project_id: str, backup_bucket: str, namespace: str = "superagi"
    ):
        self.project_id = project_id
        self.backup_bucket = backup_bucket
        self.namespace = namespace
        self.storage_client = storage.Client(project=project_id)
        self.firestore_client = firestore.Client(project=project_id)

        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        self.k8s_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()

    async def backup_dragonfly(self) -> Tuple[bool, str]:
        """Backup DragonflyDB data"""
        logger.info("Starting DragonflyDB backup...")

        try:
            # Get DragonflyDB service
            dragonfly_host = f"dragonfly.{self.namespace}.svc.cluster.local"

            # Connect to DragonflyDB
            r = redis.Redis(host=dragonfly_host, port=6379, decode_responses=True)

            # Trigger background save
            r.bgsave()

            # Wait for save to complete
            await asyncio.sleep(5)

            # Create backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"dragonfly/backup_{timestamp}.rdb"

            # Get the RDB file from the pod
            pods = self.k8s_v1.list_namespaced_pod(
                self.namespace, label_selector="app=dragonfly"
            )

            if not pods.items:
                raise Exception("No DragonflyDB pods found")

            pod_name = pods.items[0].metadata.name

            # Copy RDB file from pod
            local_path = f"/tmp/dragonfly_backup_{timestamp}.rdb"
            subprocess.run(
                [
                    "kubectl",
                    "cp",
                    f"{self.namespace}/{pod_name}:/data/dump.rdb",
                    local_path,
                ],
                check=True,
            )

            # Upload to GCS
            bucket = self.storage_client.bucket(self.backup_bucket)
            blob = bucket.blob(backup_filename)
            blob.upload_from_filename(local_path)

            # Clean up local file
            os.remove(local_path)

            logger.info(f"DragonflyDB backup completed: {backup_filename}")
            return True, backup_filename

        except Exception as e:
            logger.error(f"DragonflyDB backup failed: {str(e)}")
            return False, str(e)

    async def backup_firestore(
        self, collections: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Backup Firestore collections"""
        logger.info("Starting Firestore backup...")

        try:
            # Default collections to backup
            if not collections:
                collections = ["agents", "memories", "tools", "conversations"]

            # Create export request
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Use gcloud command for export
            cmd = [
                "gcloud",
                "firestore",
                "export",
                f"--project={self.project_id}",
                f"gs://{self.backup_bucket}/firestore/export_{timestamp}",
                "--collection-ids=" + ",".join(collections),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"Firestore export failed: {result.stderr}")

            logger.info(f"Firestore backup completed: export_{timestamp}")
            return True, f"export_{timestamp}"

        except Exception as e:
            logger.error(f"Firestore backup failed: {str(e)}")
            return False, str(e)

    async def verify_backups(self, max_age_hours: int = 24) -> Dict[str, bool]:
        """Verify recent backups exist"""
        logger.info("Verifying backups...")

        results = {"dragonfly": False, "firestore": False}

        try:
            bucket = self.storage_client.bucket(self.backup_bucket)
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            # Check DragonflyDB backups
            dragonfly_blobs = list(bucket.list_blobs(prefix="dragonfly/"))
            if dragonfly_blobs:
                latest = max(dragonfly_blobs, key=lambda b: b.time_created)
                if latest.time_created.replace(tzinfo=None) > cutoff_time:
                    results["dragonfly"] = True
                    logger.info(f"✓ Recent DragonflyDB backup found: {latest.name}")
                else:
                    logger.warning(f"⚠ DragonflyDB backup is old: {latest.name}")

            # Check Firestore backups
            firestore_blobs = list(bucket.list_blobs(prefix="firestore/"))
            if firestore_blobs:
                results["firestore"] = True
                logger.info("✓ Firestore backups found")

        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}")

        return results


async def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Orchestra Backup Manager")
    parser.add_argument("--project-id", required=True, help="GCP Project ID")
    parser.add_argument("--backup-bucket", required=True, help="GCS bucket for backups")
    parser.add_argument("--namespace", default="superagi", help="Kubernetes namespace")
    parser.add_argument("--run-backup", action="store_true", help="Run backup now")
    parser.add_argument("--verify", action="store_true", help="Verify recent backups")

    args = parser.parse_args()

    manager = BackupManager(
        project_id=args.project_id,
        backup_bucket=args.backup_bucket,
        namespace=args.namespace,
    )

    if args.run_backup:
        # Run all backups
        dragonfly_result = await manager.backup_dragonfly()
        firestore_result = await manager.backup_firestore()

        if dragonfly_result[0] and firestore_result[0]:
            logger.info("All backups completed successfully")
        else:
            logger.error("Some backups failed")
            exit(1)

    if args.verify:
        results = await manager.verify_backups()
        if all(results.values()):
            logger.info("All backups verified successfully")
        else:
            logger.error("Some backups are missing or old")
            exit(1)


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
