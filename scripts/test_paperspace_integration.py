#!/usr/bin/env python3
"""
Integration tests for Paperspace environment.
Validates service connectivity and functionality.
"""

import os
import unittest

import redis
import weaviate
from pymongo import MongoClient

class TestPaperspaceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize test environment."""
        if not os.getenv("PAPERSPACE_ENV"):
            raise unittest.SkipTest("Not running in Paperspace environment")

    def test_weaviate_connection(self):
        """Test Weaviate service connectivity."""
        client = weaviate.connect_to_local(
            host="localhost",
            port=int(os.getenv("MCP_WEAVIATE_SERVER_PORT", "8081")),
            auth=weaviate.AuthApiKey(os.getenv("PAPERSPACE_WEAVIATE_API_KEY")),
        )
        self.assertTrue(client.is_ready())
        client.close()

    def test_redis_connection(self):
        """Test Redis/DragonflyDB service connectivity."""
        r = redis.StrictRedis(
            host="localhost",
            port=int(os.getenv("MCP_REDIS_SERVER_PORT", "6379")),
            password=os.getenv("PAPERSPACE_DRAGONFLYDB_PASSWORD"),
            decode_responses=True,
        )
        self.assertTrue(r.ping())

    def test_mongodb_connection(self):
        """Test MongoDB service connectivity."""
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        self.assertEqual(client.admin.command("ping").get("ok"), 1.0)

if __name__ == "__main__":
    unittest.main()
