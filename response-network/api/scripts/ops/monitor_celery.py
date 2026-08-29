#!/usr/bin/env python
"""
Monitoring script برای بررسی وضعیت Celery
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "api"))

from workers.celery_app import celery_app
from core.config import settings

print("=" * 60)
print("🔍 Monitoring Celery Status")
print("=" * 60)

# Inspect commands
inspect = celery_app.control.inspect()

while True:
    try:
        print(f"\n⏰ Time: {time.strftime('%H:%M:%S')}")
        
        # 1. فعال بودن workers
        print("\n1️⃣ Active Workers:")
        stats = inspect.stats()
        if stats:
            for worker_name, worker_info in stats.items():
                print(f"   ✅ {worker_name} - pool: {worker_info.get('pool', {}).get('implementation')}")
        else:
            print("   ❌ هیچ Worker فعالی نیست!")
        
        # 2. تسک‌های فعال
        print("\n2️⃣ Active Tasks:")
        active = inspect.active()
        if active:
            for worker, tasks in active.items():
                print(f"   Worker: {worker}")
                for task in tasks:
                    print(f"     - {task['name']} [{task['id'][:8]}...]")
        else:
            print("   ✅ هیچ تسک فعالی نیست")
        
        # 3. Queue length
        print("\n3️⃣ Queue Status:")
        try:
            import redis
            r = redis.from_url(str(settings.REDIS_URL))
            queue_length = r.llen("celery")
            print(f"   Queue length: {queue_length}")
        except Exception as e:
            print(f"   ❌ خطا: {e}")
        
        print("\n" + "-" * 60)
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring متوقف شد")
        break
    except Exception as e:
        print(f"❌ خطا: {e}")
        time.sleep(5)
