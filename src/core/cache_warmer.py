#!/usr/bin/env python3
"""
Cache Warming Utility for Cherry AI
Pre-loads frequently accessed data into cache
"""

import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta


class CacheWarmer:
    """Warms cache with frequently accessed data"""
    
    def __init__(self, redis_client, weaviate_client):
        self.redis = redis_client
        self.weaviate = weaviate_client
        self.warming_tasks = []
    
    async def warm_agent_configs(self):
        """Pre-load agent configurations"""
        # Load agent configs from file
        with open("config/agents.yaml") as f:
            agents = yaml.safe_load(f)
        
        for agent_id, config in agents.items():
            cache_key = f"agent:config:{agent_id}"
            await self.redis.set(
                cache_key,
                json.dumps(config),
                ex=3600  # 1 hour TTL
            )
        
        print(f"  Warmed {len(agents)} agent configurations")
    
    async def warm_recent_memories(self, agent_ids: List[str]):
        """Pre-load recent memories for active agents"""
        for agent_id in agent_ids:
            # Get recent memories from Weaviate
            result = self.weaviate.query.get(
                "Memory",
                ["content", "memory_type", "importance", "timestamp"]
            ).with_where({
                "path": ["agent_id"],
                "operator": "Equal",
                "valueText": agent_id
            }).with_limit(100).do()
            
            if result and "data" in result:
                memories = result["data"]["Get"]["Memory"]
                cache_key = f"agent:memories:recent:{agent_id}"
                await self.redis.set(
                    cache_key,
                    json.dumps(memories),
                    ex=1800  # 30 minutes TTL
                )
        
        print(f"  Warmed recent memories for {len(agent_ids)} agents")
    
    async def warm_knowledge_base(self):
        """Pre-load frequently accessed knowledge"""
        # Get top knowledge items by access count
        result = self.weaviate.query.aggregate(
            "Knowledge"
        ).with_meta_count().with_group_by_filter(
            ["category"]
        ).do()
        
        if result and "data" in result:
            for category in result["data"]["Aggregate"]["Knowledge"]:
                cache_key = f"knowledge:category:{category['groupedBy']['category']}"
                await self.redis.set(
                    cache_key,
                    json.dumps(category),
                    ex=3600  # 1 hour TTL
                )
        
        print("  Warmed knowledge base categories")
    
    async def run_warming_cycle(self):
        """Run a complete cache warming cycle"""
        print("🔥 Starting cache warming cycle...")
        
        await self.warm_agent_configs()
        await self.warm_recent_memories(["cherry", "assistant", "conductor"])
        await self.warm_knowledge_base()
        
        print("✅ Cache warming complete")


async def schedule_cache_warming(warmer: CacheWarmer, interval_minutes: int = 30):
    """Schedule periodic cache warming"""
    while True:
        try:
            await warmer.run_warming_cycle()
        except Exception as e:
            print(f"Cache warming error: {e}")
        
        await asyncio.sleep(interval_minutes * 60)
