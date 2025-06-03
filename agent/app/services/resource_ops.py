def upload_resource(file):
    """Upload a new resource file (stub)."""
    return {"status": "success", "filename": file.filename}

def download_resource(resource_id: str):
    """Download a resource file (stub)."""
    return {"status": "success", "resource_id": resource_id}

def delete_resource(resource_id: str):
    """Delete a resource file (stub)."""
    return {"status": "success", "resource_id": resource_id}
