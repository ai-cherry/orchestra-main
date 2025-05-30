# Recovery Guide

This document explains how to restore the `/data` volume from a Vultr snapshot.

1. List available snapshots:
   ```bash
   vultr-cli snapshot list
   ```
2. Detach the current block storage if necessary and create a new volume from the desired snapshot:
   ```bash
   vultr-cli snapshot restore <SNAPSHOT_ID>
   ```
3. Mount the restored volume on the server at `/data`.

Ensure the server is stopped while restoring to avoid data corruption.
