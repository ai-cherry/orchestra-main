#!/usr/bin/env python3
"""
"""
    """Start an MCP server"""
    print(f"Starting {name} server...")
    try:

        pass
        env = os.environ.copy()
        process = subprocess.Popen(
            [command] + args,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception:

        pass
        print(f"Failed to start {name}: {e}")
        return None

async def main():
    """Main function to start all MCP servers"""
        ("orchestrator", "python", ["mcp_server/servers/orchestrator_server.py"]),
        ("memory", "python", ["mcp_server/servers/memory_server.py"]),
        ("weaviate", "python", ["mcp_server/servers/weaviate_direct_mcp_server.py"]),
        ("deployment", "python", ["mcp_server/servers/deployment_server.py"]),
        ("tools", "python", ["mcp_server/servers/tools_server.py"])
    ]
    
    # Start all servers
    for name, command, args in server_configs:
        process = start_server(name, command, args)
        if process:
            servers.append((name, process))
    
    print(f"\n✓ Started {len(servers)} MCP servers")
    print("\nPress Ctrl+C to stop all servers")
    
    try:

    
        pass
        # Keep running
        while True:
            await asyncio.sleep(1)
            # Check if any server has died
            for name, process in servers:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} server stopped with code {process.returncode}")
    except Exception:

        pass
        print("\n\nStopping all servers...")
        for name, process in servers:
            process.terminate()
        print("✓ All servers stopped")

if __name__ == "__main__":
    asyncio.run(main())
