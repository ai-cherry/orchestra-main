"""
"""
    """
    """
        """
        """
                """
            """
                keys = [row["key"] for row in rows]
                await self._manager.execute(
                    """
                """
            logger.error(f"Error getting cache entries by tags {tags}: {e}")
            return []

    async def cache_get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        """
                """
            """
                result[row["key"]] = row["value"]

            return result

        except Exception:


            pass
            logger.error(f"Error getting multiple cache entries: {e}")
            return {key: None for key in keys}

    async def cache_set_many(self, items: Dict[str, Any], ttl: int = 3600, tags: Optional[List[str]] = None) -> int:
        """
        """
                """
            """
            logger.info(f"Cached {count} entries in bulk operation")
            return count

        except Exception:


            pass
            logger.error(f"Error setting multiple cache entries: {e}")
            return 0

    async def cache_touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        """
                    """
                """
                    """
                """
            return result.split()[-1] != "0"

        except Exception:


            pass
            logger.error(f"Error touching cache entry {key}: {e}")
            return False

    async def cache_info(self) -> Dict[str, Any]:
        """
        """
                """
            """
                """
            """
                """
            """
                "statistics": dict(stats) if stats else {},
                "hot_keys": [dict(row) for row in hot_keys],
                "tag_distribution": [dict(row) for row in tag_dist],
                "health": {
                    "expired_ratio": (
                        float(stats["expired_entries"]) / float(stats["total_entries"])
                        if stats and stats["total_entries"] > 0
                        else 0
                    ),
                    "avg_entry_size_kb": (
                        float(stats["avg_entry_size"]) / 1024 if stats and stats["avg_entry_size"] else 0
                    ),
                    "cache_efficiency": float(stats["avg_access_count"]) if stats and stats["avg_access_count"] else 0,
                },
            }

        except Exception:


            pass
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e), "statistics": {}, "hot_keys": [], "tag_distribution": [], "health": {}}
