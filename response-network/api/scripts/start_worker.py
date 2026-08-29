#!/usr/bin/env python
"""
Worker Launcher - Automatically uses --pool=solo on Windows
"""
import sys
import os
import subprocess
import platform

def start_worker():
    """شروع Celery Worker با تنظیمات Windows-friendly"""
    
    # Change to API directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Base command
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "workers.celery_app",
        "worker",
        "--loglevel=info",
    ]
    
    # Add --pool=solo on Windows
    if platform.system() == "Windows":
        cmd.append("--pool=solo")
        print("🪟 Windows detected - using --pool=solo")
    else:
        print("🐧 Linux/Mac detected - using default pool")
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Celery Worker")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")
    
    # Start worker
    subprocess.run(cmd)

if __name__ == "__main__":
    start_worker()
