"""
"""
    """
    """
        """
        """
                """
            """
            logger.info(f"Created memory snapshot {snapshot_id} for agent {agent_id}")
            return str(snapshot_id)

        except Exception:


            pass
            logger.error(f"Error creating memory snapshot for agent {agent_id}: {e}")
            raise

    async def memory_snapshot_get(self, snapshot_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        """
                """
            """
            logger.error(f"Error getting memory snapshot {snapshot_id}: {e}")
            return None

    async def memory_snapshot_list(
        self, agent_id: Union[str, UUID], user_id: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        """
                    """
                """
                    """
                """
            logger.error(f"Error listing memory snapshots for agent {agent_id}: {e}")
            return []

    async def memory_snapshot_delete(self, snapshot_id: Union[str, UUID]) -> bool:
        """
        """
                """
            """
            deleted = result.split()[-1] != "0"
            if deleted:
                logger.info(f"Deleted memory snapshot {snapshot_id}")

            return deleted

        except Exception:


            pass
            logger.error(f"Error deleting memory snapshot {snapshot_id}: {e}")
            return False

    async def memory_snapshot_cleanup(self, days_old: int = 90, keep_minimum: int = 5) -> int:
        """
        """
                """
            """
            logger.info(f"Cleaned up {count} old memory snapshots")
            return count

        except Exception:


            pass
            logger.error(f"Error cleaning up memory snapshots: {e}")
            return 0

    async def memory_snapshot_restore(
        self, snapshot_id: Union[str, UUID], target_agent_id: Optional[Union[str, UUID]] = None
    ) -> Dict[str, Any]:
        """
        """
                raise ValueError(f"Snapshot {snapshot_id} not found")

            # Use original agent if no target specified
            if target_agent_id is None:
                target_agent_id = original["agent_id"]
            elif isinstance(target_agent_id, str):
                target_agent_id = UUID(target_agent_id)

            # Create new snapshot with restored data
            new_snapshot_id = await self.memory_snapshot_create(
                agent_id=target_agent_id,
                user_id=original.get("user_id"),
                snapshot_data=original["snapshot_data"],
                vector_ids=original.get("vector_ids"),
                metadata={
                    **original.get("metadata", {}),
                    "restored_from": str(snapshot_id),
                    "restored_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Restored snapshot {snapshot_id} to new snapshot {new_snapshot_id}")
            return await self.memory_snapshot_get(new_snapshot_id)

        except Exception:


            pass
            logger.error(f"Error restoring memory snapshot {snapshot_id}: {e}")
            raise

    async def memory_snapshot_search(
        self, query: str, agent_id: Optional[Union[str, UUID]] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        """
            agent_filter = ""

            if agent_id:
                if isinstance(agent_id, str):
                    agent_id = UUID(agent_id)
                params.insert(1, agent_id)
                agent_filter = "AND agent_id = $2"
                limit_param = "$3"
            else:
                limit_param = "$2"

            rows = await self._manager.fetch(
                f"""
            """
            logger.error(f"Error searching memory snapshots: {e}")
            return []

    async def memory_snapshot_stats(self, agent_id: Optional[Union[str, UUID]] = None) -> Dict[str, Any]:
        """
        """
            agent_filter = ""
            params = []

            if agent_id:
                if isinstance(agent_id, str):
                    agent_id = UUID(agent_id)
                params.append(agent_id)
                agent_filter = "WHERE agent_id = $1"

            stats = await self._manager.fetchrow(
                f"""
            """
                f"""
            """
                "summary": dict(stats) if stats else {},
                "size_distribution": [dict(row) for row in size_dist],
                "health": {
                    "avg_size_kb": (
                        float(stats["avg_snapshot_size"]) / 1024 if stats and stats["avg_snapshot_size"] else 0
                    ),
                    "total_size_mb": (
                        float(stats["total_snapshots"] * stats["avg_snapshot_size"]) / 1048576
                        if stats and stats["total_snapshots"] and stats["avg_snapshot_size"]
                        else 0
                    ),
                },
            }

        except Exception:


            pass
            logger.error(f"Error getting memory snapshot stats: {e}")
            return {"summary": {}, "size_distribution": [], "health": {}, "error": str(e)}

    def _format_memory_snapshot(self, row) -> Dict[str, Any]:
        """
        """
            "id": str(row["id"]),
            "agent_id": str(row["agent_id"]),
            "user_id": row.get("user_id"),
            "snapshot_data": row["snapshot_data"],
            "vector_ids": row.get("vector_ids", []),
            "metadata": row.get("metadata", {}),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "rank": float(row["rank"]) if "rank" in row else None,
        }
