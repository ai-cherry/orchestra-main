class MigrationRegistry:
    """Tracks the migration status of legacy components."""
    def __init__(self):
        self.migrated_modules = {}
        self.pending_modules = {}
        self.deprecated_modules = {}

    def register_migration(self, legacy_path, new_path, status="pending"):
        """Register a module for migration tracking."""
        entry = {
            "legacy_path": legacy_path,
            "new_path": new_path,
            "status": status
        }
        if status == "migrated":
            self.migrated_modules[legacy_path] = entry
        elif status == "deprecated":
            self.deprecated_modules[legacy_path] = entry
        else:
            self.pending_modules[legacy_path] = entry

    def summary(self):
        return {
            "migrated": list(self.migrated_modules.keys()),
            "pending": list(self.pending_modules.keys()),
            "deprecated": list(self.deprecated_modules.keys())
        } 