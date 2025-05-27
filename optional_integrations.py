"""
Centralized optional integrations for AI Orchestra.
Import from this module wherever an optional integration is needed.
Add new integrations here as the project grows.
"""

# MongoDB (for long-term memory, persistence)
try:
    import mongodb
except ImportError:
    mongodb = None

# Google Secret Manager (for secret management)
try:
    import secretmanager
except ImportError:
    secretmanager = None

# Google Cloud Monitoring
try:
    import monitoring_v3
except ImportError:
    monitoring_v3 = None

# Google Cloud Logging
try:
    import cloud_logging
except ImportError:
    cloud_logging = None

# Google Cloud Tasks
try:
    import tasks_v2
except ImportError:
    tasks_v2 = None

# Google Cloud Storage
try:
    import storage
except ImportError:
    storage = None

# Add more as needed for future integrations
