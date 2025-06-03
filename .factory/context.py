"""
"""
    """Context information for a specific Factory AI Droid."""
        """Convert context to dictionary format."""
            "droid_name": self.droid_name,
            "task_id": str(self.task_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "parent_context_id": str(self.parent_context_id) if self.parent_context_id else None,
            "child_context_ids": [str(cid) for cid in self.child_context_ids],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DroidContext":
        """Create context from dictionary format."""
            droid_name=data["droid_name"],
            task_id=UUID(data["task_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            parent_context_id=UUID(data["parent_context_id"]) if data.get("parent_context_id") else None,
            child_context_ids={UUID(cid) for cid in data.get("child_context_ids", [])},
        )

class FactoryContextManager:
    """Manages context for Factory AI Droid operations."""
    def __init__(self, config_path: Path = Path(".factory/config.yaml")):
        """
        """
        """Load Factory AI configuration."""
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception:

            pass
            logger.error(f"Failed to load config: {e}")
            return {}

    def create_context(
        self,
        droid_name: str,
        initial_data: Optional[Dict[str, Any]] = None,
        parent_context_id: Optional[UUID] = None,
    ) -> DroidContext:
        """
        """
        logger.info(f"Created context {context.task_id} for {droid_name}")
        return context

    def get_context(self, task_id: UUID) -> Optional[DroidContext]:
        """Retrieve a context by task ID."""
        """Get the active context for a specific droid."""
        """
        """
            logger.warning(f"Context {task_id} not found")
            return False

        if data_updates:
            context.data.update(data_updates)
        if metadata_updates:
            context.metadata.update(metadata_updates)

        context.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updated context {task_id}")
        return True

    def merge_contexts(self, source_ids: List[UUID], target_droid: str) -> DroidContext:
        """
        """
        merged_metadata = {"source_contexts": [str(sid) for sid in source_ids]}

        for source_id in source_ids:
            context = self.contexts.get(source_id)
            if context:
                merged_data.update(context.data)
                merged_metadata[f"from_{context.droid_name}"] = {
                    "task_id": str(context.task_id),
                    "created_at": context.created_at.isoformat(),
                }

        return self.create_context(
            droid_name=target_droid,
            initial_data=merged_data,
        )

    def get_context_chain(self, task_id: UUID) -> List[DroidContext]:
        """
        """
        """
        """
        """
        """
            logger.error(f"Failed to import context: {e}")
            return None

    def cleanup_old_contexts(self, days: int = 7) -> int:
        """
        """
        logger.info(f"Cleaned up {len(to_remove)} old contexts")
        return len(to_remove)

# Import timedelta for cleanup function
from datetime import timedelta

# Example usage
if __name__ == "__main__":
    # Initialize context manager
    manager = FactoryContextManager()

    # Create context for architect droid
    architect_ctx = manager.create_context(
        "architect",
        initial_data={
            "project_type": "web_application",
            "requirements": ["scalability", "security", "performance"],
        },
    )

    # Create child context for code droid
    code_ctx = manager.create_context(
        "code",
        initial_data={
            "language": "python",
            "framework": "fastapi",
        },
        parent_context_id=architect_ctx.task_id,
    )

    # Update context
    manager.update_context(
        code_ctx.task_id,
        data_updates={"modules_completed": ["auth", "api"]},
    )

    # Get context chain
    chain = manager.get_context_chain(code_ctx.task_id)
    print(f"Context chain length: {len(chain)}")

    # Export context
    exported = manager.export_context(code_ctx.task_id)
    print(f"Exported context: {exported[:100]}...")
