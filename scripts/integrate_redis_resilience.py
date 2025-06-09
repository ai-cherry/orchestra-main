#!/usr/bin/env python3
"""
Integrate Resilient Redis Client into MCP Servers
Updates all MCP servers to use the new resilient Redis client
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def find_redis_usage(file_path: Path) -> List[Tuple[int, str]]:
    """Find lines with Redis usage in a file."""
    redis_patterns = [
        r'import redis',
        r'redis\.Redis',
        r'redis\.from_url',
        r'redis_client\s*=',
        r'self\.redis_client\s*=',
        r'redis\.StrictRedis',
    ]
    
    matches = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            for pattern in redis_patterns:
                if re.search(pattern, line):
                    matches.append((i + 1, line.strip()))
                    break
    
    return matches

def update_mcp_server(file_path: Path) -> bool:
    """Update an MCP server file to use resilient Redis client."""
    print(f"\n📄 Processing: {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if 'from core.redis import ResilientRedisClient' in content:
        print("  ✅ Already using resilient Redis client")
        return False
    
    # Find Redis usage
    redis_usage = find_redis_usage(file_path)
    if not redis_usage:
        print("  ℹ️  No Redis usage found")
        return False
    
    print(f"  📍 Found {len(redis_usage)} Redis references:")
    for line_num, line in redis_usage:
        print(f"     Line {line_num}: {line}")
    
    # Prepare replacements
    replacements = []
    
    # Replace import statements
    replacements.append((
        r'import redis\b',
        'from core.redis import ResilientRedisClient, RedisConfig'
    ))
    
    # Replace Redis client initialization
    replacements.append((
        r'redis\.from_url\([^)]+\)',
        'ResilientRedisClient(RedisConfig.from_env())'
    ))
    
    replacements.append((
        r'redis\.Redis\([^)]*\)',
        'ResilientRedisClient(RedisConfig.from_env())'
    ))
    
    replacements.append((
        r'redis\.StrictRedis\([^)]*\)',
        'ResilientRedisClient(RedisConfig.from_env())'
    ))
    
    # Apply replacements
    modified_content = content
    changes_made = False
    
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, modified_content)
        if new_content != modified_content:
            modified_content = new_content
            changes_made = True
            print(f"  ✏️  Replaced: {pattern}")
    
    # Handle async methods
    if 'async def' in content:
        # Replace sync Redis methods with async versions
        async_replacements = [
            (r'\.get\(', '.get('),  # Already async in resilient client
            (r'\.set\(', '.set('),
            (r'\.hget\(', '.hget('),
            (r'\.hset\(', '.hset('),
            (r'\.hgetall\(', '.hgetall('),
            (r'\.delete\(', '.delete('),
            (r'\.exists\(', '.exists('),
            (r'\.expire\(', '.expire('),
            (r'\.keys\(', '.keys('),
            (r'\.incr\(', '.incr('),
            (r'\.decr\(', '.decr('),
        ]
        
        # Add await to Redis method calls in async functions
        for method, _ in async_replacements:
            # Find async function blocks
            async_func_pattern = r'(async def [^:]+:.*?)(?=\n(?:def|class|async def|\Z))'
            
            def add_await_to_redis_calls(match):
                func_block = match.group(0)
                # Add await to Redis method calls that aren't already awaited
                for redis_method, _ in async_replacements:
                    pattern = rf'(?<!await\s)(?<!await\s\s)(?<!await\s\s\s)(self\.redis_client{redis_method})'
                    func_block = re.sub(pattern, r'await \1', func_block)
                return func_block
            
            modified_content = re.sub(async_func_pattern, add_await_to_redis_calls, modified_content, flags=re.DOTALL)
    
    if changes_made:
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(modified_content)
        print("  ✅ Updated to use resilient Redis client")
        return True
    
    return False

def main():
    """Main function to update all MCP servers."""
    print("🚀 Integrating Resilient Redis Client into MCP Servers")
    print("=" * 60)
    
    # Find all MCP server files
    mcp_server_dir = Path("mcp_server/servers")
    if not mcp_server_dir.exists():
        print("❌ MCP server directory not found!")
        return
    
    server_files = list(mcp_server_dir.glob("*_server.py"))
    print(f"📁 Found {len(server_files)} MCP server files")
    
    # Update each server
    updated_count = 0
    for server_file in server_files:
        if update_mcp_server(server_file):
            updated_count += 1
    
    # Also update other files that use Redis
    other_files = [
        Path("mcp_server/storage/async_memory_store.py"),
    ]
    
    print("\n📄 Checking other Redis-using files...")
    for file_path in other_files:
        if file_path.exists():
            if update_mcp_server(file_path):
                updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Integration complete! Updated {updated_count} files")
    
    if updated_count > 0:
        print("\n📋 Next steps:")
        print("1. Test the updated services:")
        print("")
        print("\n2. Restart MCP servers to use new Redis client:")
        print("   docker-compose -f docker-compose.single-user.yml restart")
        print("\n3. Monitor Redis health:")
        print("   curl http://localhost:8010/health")

if __name__ == "__main__":
    main()