import os
import time
import httpx

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
QUERY = {"query": "hello"}

async def measure_latency() -> float:
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{WEAVIATE_URL}/v1/graphql", json=QUERY)
        r.raise_for_status()
    return time.perf_counter() - start

if __name__ == "__main__":
    import asyncio

    lat = asyncio.run(measure_latency())
    print(f"Latency: {lat:.3f}s")
