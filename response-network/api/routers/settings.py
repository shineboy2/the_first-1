from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict

from api.auth.dependencies import verify_api_key
from workers.tasks.settings_exporter import export_settings_to_request_network

router = APIRouter(prefix="/settings", tags=["settings"])

@router.post("/export", response_model=Dict[str, str])
async def trigger_settings_export(
    background_tasks: BackgroundTasks,
    _: None = Depends(verify_api_key),
) -> Dict[str, str]:
    """
    Manually trigger settings export to request network.
    Requires valid API key authentication.
    """
    # Run the export task in the background
    task = export_settings_to_request_network.delay()
    
    return {"message": "Settings export started", "task_id": str(task.id)}