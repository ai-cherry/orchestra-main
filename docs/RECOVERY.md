# Recovery Guide

This document explains how to restore the `/data` volume from a Vultr snapshot.

Snapshots are created automatically each night via `/root/snapshot.sh`, which is
installed by Pulumi and scheduled by cron at 03:00 UTC. You can also run this
script manually if needed.

1. List available snapshots:
   ```bash
   vultr-cli snapshot list
   ```
2. Detach the current block storage if necessary and create a new volume from the desired snapshot:
   ```bash
   vultr-cli snapshot restore <SNAPSHOT_ID>
   ```
3. Mount the restored volume on the server at `/data`.

To trigger a manual snapshot at any time:
```bash
sudo /root/snapshot.sh
```

Ensure the server is stopped while restoring to avoid data corruption.
