"""
Admin endpoints for task queue management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from auth.dependencies import get_current_user
from models.user import User
from schemas.task_management import QueueStats, TaskInfo, TaskAction, WorkerStats
from workers.celery_app import celery_app
import redis

router = APIRouter(
    prefix="/admin/tasks",
    tags=["admin-tasks"],
    dependencies=[Depends(get_current_user)]
)

# Redis client
from core.config import settings
redis_client = redis.from_url(str(settings.REDIS_URL))

def get_inspect():
    return celery_app.control.inspect()


async def check_admin(user: User = Depends(get_current_user)):
    """بررسی کنید که user admin است"""
    if not user or user.profile_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="تنها ادمین‌ها می‌توانند queue را مدیریت کنند"
        )
    return user


@router.get("/queue/stats", response_model=QueueStats)
async def get_queue_stats(admin: User = Depends(check_admin)):
    """
    مشاهده آمار Queue و Tasks فعال
    
    - **total_queued**: تعداد tasks در صف
    - **total_active**: تعداد tasks در حال اجرا
    - **active_workers**: تعداد workers فعال
    """
    try:
        # تعداد tasks در صف
        queue_length = redis_client.llen("celery")
        
        # tasks فعال
        inspect = get_inspect()
        active = inspect.active()
        total_active = sum(len(tasks) for tasks in active.values()) if active else 0
        active_workers = len(active) if active else 0
        
        # جزئیات tasks فعال
        active_tasks = []
        if active:
            for worker_name, tasks in active.items():
                for task in tasks:
                    active_tasks.append(TaskInfo(
                        task_id=task['id'],
                        name=task['name'],
                        state='STARTED',
                        args=task.get('args'),
                        kwargs=task.get('kwargs'),
                        worker=worker_name
                    ))
        
        return QueueStats(
            total_queued=queue_length,
            total_active=total_active,
            active_workers=active_workers,
            details=active_tasks
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت آمار: {str(e)}"
        )


@router.get("/workers/stats", response_model=List[WorkerStats])
async def get_workers_stats(admin: User = Depends(check_admin)):
    """
    مشاهده آمار تمام Workers
    
    - **worker_name**: نام worker
    - **pool_type**: نوع pool (solo, prefork, etc)
    - **max_concurrency**: حداکثر concurrent tasks
    - **active_tasks**: tasks در حال اجرا در این worker
    """
    try:
        inspect = get_inspect()
        stats = inspect.stats()
        worker_list = []
        
        if stats:
            for worker_name, worker_info in stats.items():
                pool_info = worker_info.get('pool', {})
                active = inspect.active()
                active_count = len(active.get(worker_name, [])) if active else 0
                
                # Calculate total processed tasks
                total_info = worker_info.get('total', {})
                if isinstance(total_info, dict):
                    # Sum all task counts from the total dict
                    processed_count = sum(total_info.values()) if total_info else 0
                else:
                    processed_count = 0
                
                worker_list.append(WorkerStats(
                    worker_name=worker_name,
                    pool_type=pool_info.get('implementation', 'prefork'),
                    max_concurrency=pool_info.get('max-concurrency', 0),
                    active_tasks=active_count,
                    processed_tasks=processed_count,
                    offline=False
                ))
        
        return worker_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت آمار workers: {str(e)}"
        )


@router.get("/queue/pending")
async def get_pending_tasks(
    limit: int = 100,
    admin: User = Depends(check_admin)
):
    """
    مشاهده tasks منتظر در صف
    
    - **limit**: حداکثر تعداد tasks برای نمایش
    """
    try:
        # دریافت tasks از Redis queue
        tasks = redis_client.lrange("celery", 0, limit - 1)
        
        task_list = []
        for task_data in tasks:
            # هر task یک JSON string است
            import json
            try:
                task_json = json.loads(task_data)
                task_list.append({
                    "id": task_json.get('headers', {}).get('id', 'unknown'),
                    "name": task_json.get('headers', {}).get('task', 'unknown'),
                    "state": "PENDING",
                    "eta": task_json.get('headers', {}).get('eta'),
                    "args": task_json.get('args', []),
                    "kwargs": task_json.get('kwargs', {})
                })
            except:
                pass
        
        return {
            "total_pending": redis_client.llen("celery"),
            "shown": len(task_list),
            "tasks": task_list
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت tasks: {str(e)}"
        )


@router.post("/tasks/{task_id}/skip", response_model=TaskAction)
async def skip_task(
    task_id: str,
    admin: User = Depends(check_admin)
):
    """
    Skip کردن یک task (بدون اجرا)
    
    - **task_id**: شناسه task
    """
    try:
        # Revoke task (باعث می‌شود task اجرا نشود)
        celery_app.control.revoke(task_id, terminate=True)
        
        return TaskAction(
            task_id=task_id,
            action="skip",
            status="success",
            message=f"Task {task_id} با موفقیت skip شد"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در skip کردن task: {str(e)}"
        )


@router.delete("/queue/clear", response_model=dict)
async def clear_queue(
    confirm: bool = False,
    admin: User = Depends(check_admin)
):
    """
    پاک کردن تمام tasks از صف
    
    ⚠️ احتیاط: این عملیات غیرقابل بازگشت است!
    
    - **confirm**: باید True باشد برای تایید
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="برای تایید، confirm=true ارسال کنید"
        )
    
    try:
        count = redis_client.llen("celery")
        redis_client.delete("celery")
        
        return {
            "status": "success",
            "message": f"{count} tasks از صف حذف شد",
            "cleared_count": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در پاک کردن queue: {str(e)}"
        )


@router.post("/tasks/{task_id}/retry", response_model=TaskAction)
async def retry_task(
    task_id: str,
    admin: User = Depends(check_admin)
):
    """
    دوبارہ اجرای یک task
    
    - **task_id**: شناسه task
    """
    try:
        # Inspect برای پیدا کردن task info
        inspect = get_inspect()
        reserved = inspect.reserved()
        active = inspect.active()
        
        task_info = None
        
        # جستجو در reserved و active tasks
        if reserved:
            for worker, tasks in reserved.items():
                for task in tasks:
                    if task['id'] == task_id:
                        task_info = task
                        break
        
        if not task_info and active:
            for worker, tasks in active.items():
                for task in tasks:
                    if task['id'] == task_id:
                        task_info = task
                        break
        
        if not task_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} یافت نشد"
            )
        
        # Re-queue task
        task_name = task_info['name']
        args = task_info.get('args', [])
        kwargs = task_info.get('kwargs', {})
        
        # Call task again
        celery_app.send_task(task_name, args=args, kwargs=kwargs)
        
        return TaskAction(
            task_id=task_id,
            action="retry",
            status="success",
            message=f"Task {task_name} دوباره صف‌بندی شد"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در retry task: {str(e)}"
        )
