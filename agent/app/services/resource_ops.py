def upload_resource(file):
    """Upload a new resource file (stub)."""
    # TODO: Implement real upload logic
    return {"status": "success", "filename": file.filename}


def download_resource(resource_id: str):
    """Download a resource file (stub)."""
    # TODO: Implement real download logic
    return {"status": "success", "resource_id": resource_id}


def delete_resource(resource_id: str):
    """Delete a resource file (stub)."""
    # TODO: Implement real delete logic
    return {"status": "success", "resource_id": resource_id}
