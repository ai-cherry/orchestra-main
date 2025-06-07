"""Central API router registry to prevent endpoint conflicts"""
    """Registry to track and prevent duplicate API endpoints"""
        """Register an endpoint to check for duplicates"""
            key = f"{method}:{path}"
            if key in self.endpoints:
                logger.warning(f"Duplicate endpoint detected: {key} in {module} (already in {self.endpoints[key]})")
                return False
            self.endpoints[key] = module
        return True
    
    def get_router(self, module: str, prefix: str = "") -> APIRouter:
        """Get or create a router for a module"""