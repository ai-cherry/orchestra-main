import asyncio
import io
import zipfile
from pathlib import Path

from shared.data_ingestion.zip_processor import ZipProcessor
from shared.data_ingestion.base_processor import StorageAdapter


class InMemoryAdapter(StorageAdapter):
    def __init__(self):
        self.records = {}

    async def exists(self, fingerprint: str) -> bool:
        return fingerprint in self.records

    async def upsert_batch(self, records):
        for r in records:
            self.records[r["_fingerprint"]] = r

    async def close(self):
        pass


def create_zip(tmp_path: Path):
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("hello")
    file2.write_text("hello")  # duplicate content

    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as zf:
        zf.write(file1, arcname="a.txt")
        zf.write(file2, arcname="b.txt")
    data.seek(0)
    return data


def test_zip_dedup(tmp_path):
    adapter = InMemoryAdapter()
    processor = ZipProcessor(storage_adapter=adapter)
    zdata = create_zip(tmp_path)

    total = asyncio.run(processor.ingest(zdata))

    assert total == 1
    assert len(adapter.records) == 1
