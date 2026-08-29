#!/usr/bin/env python
"""
Quick start script - Clean Redis and start everything
"""
import sys
import os
import subprocess
import redis
import time

def clear_redis():
    """Redis queue را پاک کن"""
    try:
        r = redis.from_url("redis://localhost:6380/0")
        # پاک کن تمام queues
        for queue in ['celery', 'default']:
            count = r.llen(queue)
            if count > 0:
                r.delete(queue)
                print(f"✅ Cleared queue '{queue}' ({count} tasks)")
        
        # چک کن اگر Redis خالی است
        all_keys = r.keys('*')
        print(f"✅ Redis cleaned! Remaining keys: {len(all_keys)}")
        return True
    except Exception as e:
        print(f"❌ Redis error: {e}")
        print("⚠️  Make sure Redis is running on localhost:6380")
        return False

def start_component(script_name, description):
    """یک component را شروع کن"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    subprocess.Popen([sys.executable, script_path])
    time.sleep(2)  # زمان برای شروع

if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚡ Response Network - Quick Start")
    print("="*60)
    
    # Step 1: Clear Redis
    print("\n1️⃣  Clearing Redis...")
    if not clear_redis():
        sys.exit(1)
    
    time.sleep(1)
    
    # Step 2: Start Beat
    print("\n2️⃣  Starting Beat Scheduler...")
    start_component("start_beat.py", "Celery Beat Scheduler")
    
    # Step 3: Start Worker
    print("\n3️⃣  Starting Worker...")
    start_component("start_worker.py", "Celery Worker")
    
    # Step 4: Start API
    print("\n4️⃣  Starting FastAPI...")
    print(f"\n{'='*60}")
    print(f"🚀 FastAPI Server")
    print(f"{'='*60}")
    api_path = os.path.join(os.path.dirname(__file__), "main.py")
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"])
