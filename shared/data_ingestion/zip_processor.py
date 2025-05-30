"""ZIP file ingestion processor for Orchestra AI."""

import hashlib
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from .base_processor import BaseProcessor


class ZipProcessor(BaseProcessor):
    """Unpack ZIP archives and feed contained files to existing processors."""

    async def ingest(self, source: Any, **kwargs) -> int:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(source) as zf:
                zf.extractall(tmpdir)

            total = 0
            for fp in Path(tmpdir).rglob("*"):
                if fp.is_file():
                    digest = hashlib.sha256(fp.read_bytes()).hexdigest()
                    if await self.storage.exists(digest):
                        continue
                    await self.storage.upsert_batch([{"path": str(fp), "_fingerprint": digest}])
                    total += 1
            return total
