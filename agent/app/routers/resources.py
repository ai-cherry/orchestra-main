from fastapi import APIRouter, UploadFile, File
from agent.app.services.resource_ops import upload_resource, download_resource, delete_resource

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/upload")
async def api_upload_resource(file: UploadFile = File(...)):
    """Upload a new resource file."""
    return upload_resource(file)


@router.get("/{resource_id}/download")
async def api_download_resource(resource_id: str):
    """Download a resource file."""
    return download_resource(resource_id)


@router.delete("/{resource_id}/delete")
async def api_delete_resource(resource_id: str):
    """Delete a resource file."""
    return delete_resource(resource_id)
