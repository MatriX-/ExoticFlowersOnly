import logging
import schedule
import time
import threading
import os
import signal
from pathlib import Path
from datetime import datetime, timedelta
from src.processor import sync_sheets

logger = logging.getLogger(__name__)
PID_FILE = Path('logs/scheduler.pid')
scheduler_thread = None
stop_scheduler = threading.Event()

def scheduled_sync():
    logger.info(f"Running scheduled sync at {datetime.now()}")
    sync_sheets()

def start_scheduler():
    global scheduler_thread
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.warning("Scheduler is already running")
        return False
    
    stop_scheduler.clear()
    
    schedule.clear()
    schedule.every(1).hours.do(scheduled_sync)
    
    def run_scheduler():
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info("Scheduler started - will sync every hour")
        logger.info(f"Next sync scheduled for: {datetime.now() + timedelta(hours=1)}")
        
        while not stop_scheduler.is_set():
            schedule.run_pending()
            time.sleep(60)
        
        if PID_FILE.exists():
            PID_FILE.unlink()
        logger.info("Scheduler stopped")
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    return True

def stop_scheduler_func():
    global scheduler_thread
    
    if not scheduler_thread or not scheduler_thread.is_alive():
        logger.warning("Scheduler is not running")
        return False
    
    stop_scheduler.set()
    scheduler_thread.join(timeout=5)
    
    if PID_FILE.exists():
        PID_FILE.unlink()
    
    return True

def get_scheduler_status():
    if scheduler_thread and scheduler_thread.is_alive():
        next_run = schedule.next_run()
        if next_run:
            return {
                'running': True,
                'next_sync': next_run.isoformat()
            }
    return {'running': False, 'next_sync': None}

def cleanup_on_exit(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    stop_scheduler_func()
    exit(0)

signal.signal(signal.SIGINT, cleanup_on_exit)
signal.signal(signal.SIGTERM, cleanup_on_exit)