from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from workers.celery_app import celery_app
from redbeat import RedBeatSchedulerEntry

from auth.dependencies import get_current_admin_user
from models.user import User as UserModel

router = APIRouter(prefix="/admin/celery", tags=["Admin Celery"])

class ScheduleUpdate(BaseModel):
    interval: int

@router.get("/schedules")
async def get_schedules(current_user: UserModel = Depends(get_current_admin_user)):
    """
    Get all Celery Beat schedules from Redis via RedBeat.
    """
    try:
        from redbeat.schedulers import get_redis
        conf = celery_app.conf
        # Get all redbeat keys
        try:
            redis = get_redis(celery_app)
        except Exception:
            import redis as redis_lib
            redis = redis_lib.from_url(conf.broker_url, decode_responses=True)
            
        key_prefix = conf.get('redbeat_key_prefix', 'redbeat:')
        keys = redis.keys(f"{key_prefix}*")
        
        schedules = []
        for key in keys:
            key_str = key if isinstance(key, str) else key.decode('utf-8')
            # Extract name from key
            name = key_str.replace(key_prefix, '')
            
            # Skip non-entry keys
            if name.endswith(':meta') or name == ':schedule' or name == ':lock':
                continue
            
            try:
                entry = RedBeatSchedulerEntry.from_key(key_str, app=celery_app)
                schedules.append({
                    "name": entry.name,
                    "task": entry.task,
                    "interval": entry.schedule.run_every.total_seconds() if hasattr(entry.schedule, 'run_every') else None,
                    "enabled": True, # redbeat entries are active if they exist
                })
            except Exception as e:
                print(f"Failed to load schedule {name}: {e}")
                
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/schedules/{name}")
async def update_schedule(name: str, schedule_data: ScheduleUpdate, current_user: UserModel = Depends(get_current_admin_user)):
    """
    Update a specific schedule's interval (in seconds).
    """
    try:
        from celery.schedules import schedule
        
        # Load the entry
        key_prefix = celery_app.conf.get('redbeat_key_prefix', 'redbeat:')
        key = f"{key_prefix}{name}"
        
        entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
        
        # Update interval
        if schedule_data.interval <= 0:
            raise HTTPException(status_code=400, detail="Interval must be > 0")
            
        entry.schedule = schedule(run_every=schedule_data.interval)
        entry.save()
        
        return {"message": f"Schedule {name} updated successfully to {schedule_data.interval} seconds."}
    except KeyError:
         raise HTTPException(status_code=404, detail="Schedule not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
