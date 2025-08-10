import logging
from datetime import datetime
from pathlib import Path
from src.sheets_api import (
    get_target_sheet_id,
    create_target_sheet,
    copy_source_sheet,
    process_and_update_sheet
)

logger = logging.getLogger(__name__)
LAST_SYNC_FILE = Path('logs/last_sync.txt')

def sync_sheets():
    try:
        logger.info("Starting sheet sync process...")
        
        logger.info("Copying source sheet data...")
        source_data = copy_source_sheet()
        
        target_sheet_id = get_target_sheet_id()
        if not target_sheet_id:
            logger.info("Target sheet not found, creating new one...")
            target_sheet_id = create_target_sheet()
        else:
            logger.info(f"Found existing target sheet: {target_sheet_id}")
        
        logger.info("Processing and updating target sheet...")
        process_and_update_sheet(source_data, target_sheet_id)
        
        LAST_SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LAST_SYNC_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
        
        logger.info("Sync completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False

def get_last_sync_time():
    if LAST_SYNC_FILE.exists():
        with open(LAST_SYNC_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    return None