"""
"""
    """
    """
        """
        """
            conditions = ["is_active = true", "expires_at > CURRENT_TIMESTAMP"]
            params = []
            param_count = 0

            if user_id:
                param_count += 1
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)

            if agent_id:
                param_count += 1
                conditions.append(f"agent_id = ${param_count}")
                params.append(agent_id)

            # Add limit and offset
            param_count += 1
            limit_param = param_count
            params.append(limit)

            param_count += 1
            offset_param = param_count
            params.append(offset)

            where_clause = " AND ".join(conditions)

            rows = await self._manager.fetch(
                f"""
            """
            logger.error(f"Error listing sessions: {e}")
            return []

    async def session_extend(self, session_id: str, additional_ttl: int = 3600) -> bool:
        """
        """
                """
            """
            return result.split()[-1] != "0"

        except Exception:


            pass
            logger.error(f"Error extending session {session_id}: {e}")
            return False

    async def session_touch(self, session_id: str) -> bool:
        """
        """
                """
            """
            return result.split()[-1] != "0"

        except Exception:


            pass
            logger.error(f"Error touching session {session_id}: {e}")
            return False

    async def session_bulk_delete(self, session_ids: List[str]) -> int:
        """
        """
                """
            """
            logger.info(f"Bulk deleted {count} sessions")
            return count

        except Exception:


            pass
            logger.error(f"Error bulk deleting sessions: {e}")
            return 0

    async def session_get_active_count(
        self, user_id: Optional[str] = None, agent_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        """
            conditions = ["is_active = true", "expires_at > CURRENT_TIMESTAMP"]
            params = []

            if user_id:
                conditions.append(f"user_id = ${len(params) + 1}")
                params.append(user_id)

            if agent_id:
                conditions.append(f"agent_id = ${len(params) + 1}")
                params.append(agent_id)

            where_clause = " AND ".join(conditions)

            result = await self._manager.fetchrow(
                f"""
            """
                "total_active": result["total_active"] or 0,
                "unique_users": result["unique_users"] or 0,
                "unique_agents": result["unique_agents"] or 0,
                "avg_interactions": float(result["avg_interactions"] or 0),
            }

        except Exception:


            pass
            logger.error(f"Error getting active session count: {e}")
            return {"total_active": 0, "unique_users": 0, "unique_agents": 0, "avg_interactions": 0.0}

    def _format_session(self, row) -> Dict[str, Any]:
        """
        """
            "id": row["id"],
            "user_id": row["user_id"],
            "agent_id": row["agent_id"],
            "data": row["data"],
            "metadata": row.get("metadata", {}),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
            "ip_address": str(row["ip_address"]) if row.get("ip_address") else None,
            "user_agent": row.get("user_agent"),
            "interaction_count": row.get("interaction_count", 0),
        }
