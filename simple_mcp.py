#!/usr/bin/env python3
"""
"""
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("simple-mcp")

class SimpleMemoryStore:
    """Simple in-memory store without complex security and synchronization."""
        """Initialize the memory store."""
        """Load existing memory items from storage."""
            memory_files = list(self.storage_path.glob("*.json"))
            logger.info(f"Loading {len(memory_files)} memory files")

            for memory_file in memory_files:
                try:

                    pass
                    with open(memory_file, "r") as f:
                        memory_data = json.load(f)
                        key = memory_file.stem
                        self.memory_cache[key] = memory_data["content"]
                except Exception:

                    pass
                    logger.error(f"Error loading {memory_file}: {e}")
        except Exception:

            pass
            logger.error(f"Error loading memory: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get a memory item."""
        memory_file = self.storage_path / f"{key}.json"
        if memory_file.exists():
            try:

                pass
                with open(memory_file, "r") as f:
                    memory_data = json.load(f)
                    self.memory_cache[key] = memory_data["content"]
                    return memory_data["content"]
            except Exception:

                pass
                logger.error(f"Error reading {memory_file}: {e}")

        return None

    def set(self, key: str, content: Any) -> bool:
        """Set a memory item."""
            "content": content,
            "created": datetime.now().isoformat(),
        }

        # Write to storage
        memory_file = self.storage_path / f"{key}.json"
        try:

            pass
            with open(memory_file, "w") as f:
                json.dump(memory_data, f, indent=2)
            return True
        except Exception:

            pass
            logger.error(f"Error writing {memory_file}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a memory item."""
        memory_file = self.storage_path / f"{key}.json"
        if memory_file.exists():
            try:

                pass
                memory_file.unlink()
                return True
            except Exception:

                pass
                logger.error(f"Error deleting {memory_file}: {e}")
                return False

        return True

class SimpleMCPServer:
    """Simplified MCP Server without excessive security measures."""
    def __init__(self, storage_path: str = "./.mcp_memory", port: int = 8080):
        """Initialize the MCP server."""
        logger.info("Simple MCP server initialized")

    def _configure_routes(self):
        """Configure Flask routes."""
        @self.app.route("/api/status", methods=["GET"])
        def status():
            return jsonify(
                {
                    "status": "running",
                    "server_type": "simple_mcp",
                }
            )

        @self.app.route("/api/memory", methods=["GET"])
        def get_memory():
            key = request.args.get("key")

            if not key:
                return jsonify({"error": "Missing key parameter"}), 400

            content = self.memory_store.get(key)
            if content is None:
                return jsonify({"error": "Memory item not found"}), 404

            return jsonify({"content": content})

        @self.app.route("/api/memory", methods=["POST"])
        def set_memory():
            data = request.json
            if not data:
                return jsonify({"error": "Missing request body"}), 400

            key = data.get("key")
            content = data.get("content")

            if not key or content is None:
                return jsonify({"error": "Missing key or content parameter"}), 400

            result = self.memory_store.set(key, content)
            if not result:
                return jsonify({"error": "Failed to set memory item"}), 500

            return jsonify({"success": True})

        @self.app.route("/api/memory", methods=["DELETE"])
        def delete_memory():
            key = request.args.get("key")

            if not key:
                return jsonify({"error": "Missing key parameter"}), 400

            result = self.memory_store.delete(key)
            if not result:
                return jsonify({"error": "Failed to delete memory item"}), 500

            return jsonify({"success": True})

    def run(self):
        """Run the MCP server."""
        logger.info(f"Starting Simple MCP server on port {self.port}")
        self.app.run(host="0.0.0.0", port=self.port, debug=False)

def main():
    """Main entry point for the Simple MCP server."""
    parser = argparse.ArgumentParser(description="Simple Model Context Protocol (MCP) Server")
    parser.add_argument("--storage", default="./.mcp_memory", help="Path to storage directory")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")

    args = parser.parse_args()

    # Create and run server
    server = SimpleMCPServer(storage_path=args.storage, port=args.port)
    server.run()

if __name__ == "__main__":
    main()
