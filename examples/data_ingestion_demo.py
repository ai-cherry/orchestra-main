#!/usr/bin/env python3
"""
Orchestra AI Data Ingestion Demo
Demonstrates various data ingestion capabilities.
"""

import asyncio
import json

# Add parent directory to path for imports
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from shared.data_ingestion.ingestion_pipeline import DataIngestionPipeline


async def demo_file_ingestion(pipeline: DataIngestionPipeline) -> None:
    """Demonstrate file ingestion capabilities."""
    print("\n=== FILE INGESTION DEMO ===")

    # Create sample data files
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)

    # Create CSV file
    csv_file = sample_dir / "sales_data.csv"
    csv_file.write_text(
        """date,product,quantity,price
2024-01-01,Widget A,100,29.99
2024-01-02,Widget B,75,39.99
2024-01-03,Widget A,120,29.99
2024-01-04,Widget C,50,49.99
2024-01-05,Widget B,90,39.99"""
    )

    # Create JSON file
    json_file = sample_dir / "customer_data.json"
    json_file.write_text(
        json.dumps(
            {
                "customers": [
                    {
                        "id": 1,
                        "name": "Alice",
                        "email": "alice@example.com",
                        "orders": 5,
                    },
                    {"id": 2, "name": "Bob", "email": "bob@example.com", "orders": 3},
                    {
                        "id": 3,
                        "name": "Charlie",
                        "email": "charlie@example.com",
                        "orders": 7,
                    },
                ],
                "metadata": {"exported": "2024-01-15", "version": "1.0"},
            },
            indent=2,
        )
    )

    # Create XML file
    xml_file = sample_dir / "inventory.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<inventory>
    <item id="001">
        <name>Widget A</name>
        <stock>500</stock>
        <location>Warehouse A</location>
    </item>
    <item id="002">
        <name>Widget B</name>
        <stock>300</stock>
        <location>Warehouse B</location>
    </item>
</inventory>"""
    )

    # Ingest CSV file
    print("\n1. Ingesting CSV file...")
    csv_results = await pipeline.ingest_file(
        csv_file, processor_kwargs={"chunk_size": 2}
    )  # Small chunk for demo
    print(f"   - Processed {len(csv_results)} chunks from CSV")

    # Ingest JSON file
    print("\n2. Ingesting JSON file...")
    json_results = await pipeline.ingest_file(
        json_file, processor_kwargs={"flatten": True}
    )
    print(f"   - Processed {len(json_results)} items from JSON")

    # Ingest XML file
    print("\n3. Ingesting XML file...")
    xml_results = await pipeline.ingest_file(
        xml_file, processor_kwargs={"xpath_filter": ".//item"}
    )
    print(f"   - Processed {len(xml_results)} items from XML")

    # Ingest entire directory
    print("\n4. Ingesting entire directory...")
    dir_results = await pipeline.ingest_directory(sample_dir, recursive=False)
    print(f"   - Processed {len(dir_results)} files from directory")
    for file_path, results in dir_results.items():
        print(f"     - {Path(file_path).name}: {len(results)} items")


async def demo_api_ingestion(pipeline: DataIngestionPipeline) -> None:
    """Demonstrate API ingestion capabilities."""
    print("\n=== API INGESTION DEMO ===")

    # Example: JSONPlaceholder API (free test API)
    print("\n1. Ingesting from REST API (JSONPlaceholder)...")

    try:
        # Fetch posts with pagination
        api_results = await pipeline.ingest_api(
            api_type="rest",
            url="https://jsonplaceholder.typicode.com",
            processor_kwargs={
                "endpoint": "/posts",
                "method": "GET",
                "pagination_type": "none",  # This API doesn't paginate
                "params": {"_limit": 5},  # Limit for demo
            },
        )
        print(f"   - Fetched {len(api_results)} posts from API")

        # Show sample data
        if api_results:
            first_item = json.loads(api_results[0].raw_content)
            print(f"   - Sample post title: '{first_item.get('title', 'N/A')}'")

    except Exception as e:
        print(f"   - API demo failed: {e}")
        print("   - Note: Requires internet connection")


async def demo_batch_ingestion(pipeline: DataIngestionPipeline) -> None:
    """Demonstrate batch ingestion capabilities."""
    print("\n=== BATCH INGESTION DEMO ===")

    # Prepare batch sources
    sample_dir = Path("sample_data")

    batch_sources = [
        {
            "type": "file",
            "source": str(sample_dir / "sales_data.csv"),
            "kwargs": {"delimiter": ","},
        },
        {
            "type": "file",
            "source": str(sample_dir / "customer_data.json"),
            "kwargs": {"flatten": False},
        },
        {
            "type": "api",
            "api_type": "rest",
            "source": "https://jsonplaceholder.typicode.com",
            "kwargs": {"endpoint": "/users", "method": "GET", "params": {"_limit": 3}},
        },
    ]

    print("\n1. Processing batch of mixed sources...")
    batch_results = await pipeline.ingest_batch(
        batch_sources, parallel=True, max_concurrent=3
    )

    print(f"   - Processed {len(batch_results)} sources")
    for source_id, results in batch_results.items():
        source_type = "File" if "/" in source_id else "API"
        print(f"     - {source_type}: {len(results)} items")


async def demo_statistics(pipeline: DataIngestionPipeline) -> None:
    """Show ingestion statistics."""
    print("\n=== INGESTION STATISTICS ===")

    stats = pipeline.get_ingestion_stats()

    print("\n1. Backend Health:")
    for backend, status in stats["backends_health"].items():
        status_str = "✓ Online" if status else "✗ Offline"
        print(f"   - {backend}: {status_str}")

    print("\n2. Available Processors:")
    print(f"   - File types: {', '.join(stats['processors_available']['file_types'])}")
    print(f"   - API types: {', '.join(stats['processors_available']['api_types'])}")


async def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("ORCHESTRA AI DATA INGESTION DEMONSTRATION")
    print("=" * 60)

    # Initialize pipeline
    print("\nInitializing data ingestion pipeline...")
    pipeline = DataIngestionPipeline(
        enable_embedding_generation=False, batch_size=10
    )  # Disabled for demo

    try:
        # Run demonstrations
        await demo_file_ingestion(pipeline)
        await demo_api_ingestion(pipeline)
        await demo_batch_ingestion(pipeline)
        await demo_statistics(pipeline)

    finally:
        # Cleanup
        print("\n\nCleaning up...")
        pipeline.shutdown()

        # Remove sample data
        sample_dir = Path("sample_data")
        if sample_dir.exists():
            import shutil

            shutil.rmtree(sample_dir)

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
