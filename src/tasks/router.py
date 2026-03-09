from fastapi import APIRouter, HTTPException, Query
from tasks.tasks import delete_expired_links, cleanup_unused_links
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/cleanup/expired")
async def manual_cleanup_expired():
    try:
        task = delete_expired_links.delay()
        return {
            "message": "Cleanup task started",
            "task_id": task.id,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup/unused")
async def manual_cleanup_unused(
    days: int = Query(30, description="Количество дней без использования после которого ссылка удаляется")
):
    try:
        task = cleanup_unused_links.delay(days)
        return {
            "message": f"Cleanup unused links (>{days} days) task started",
            "task_id": task.id,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    from celery.result import AsyncResult
    from tasks.tasks import celery
    
    task = AsyncResult(task_id, app=celery)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }

@router.get("/settings")
async def get_cleanup_settings():
    return {
        "unused_links_days": 30,
        "schedule": "daily"
    }
