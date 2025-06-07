# TODO: Consider adding connection pooling configuration
"""
"""
    """Types of storage backends supported."""
    POSTGRES = "postgres"
    WEAVIATE = "weaviate"
    REDIS = "redis"

@dataclass
class StorageResult:
    """
    """
        """Initialize metadata if not provided."""
    """
    """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
            test_key = f"_health_check_{datetime.utcnow().timestamp()}"
            result = await self.store("test", key=test_key)
            
            if result.success:
                await self.delete(test_key)
                return {
                    "healthy": True,
                    "storage_type": self.storage_type.value if self.storage_type else "unknown",
                    "connected": self._connected,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "healthy": False,
                    "error": result.error,
                    "storage_type": self.storage_type.value if self.storage_type else "unknown",
                    "connected": self._connected,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception:

            pass
            return {
                "healthy": False,
                "error": str(e),
                "storage_type": self.storage_type.value if self.storage_type else "unknown",
                "connected": self._connected,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def is_connected(self) -> bool:
        """Check if the storage backend is connected."""