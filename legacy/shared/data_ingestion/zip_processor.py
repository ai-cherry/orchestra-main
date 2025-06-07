"""ZIP file ingestion processor for Cherry AI."""
    """Unpack ZIP archives and feed contained files to existing processors."""
            for fp in Path(tmpdir).rglob("*"):
                if fp.is_file():
                    digest = hashlib.sha256(fp.read_bytes()).hexdigest()
                    if await self.storage.exists(digest):
                        continue
                    await self.storage.upsert_batch([{"path": str(fp), "_fingerprint": digest}])
                    total += 1
            return total
