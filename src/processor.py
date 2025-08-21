import logging
from datetime import datetime
from pathlib import Path
from src.sheets_api import (
    get_target_sheet_id,
    create_target_sheet,
    copy_source_sheet,
    process_and_update_sheet
)
from src.menu_configs import get_menu_config

logger = logging.getLogger(__name__)

def sync_sheets(menu_type='thca'):
    try:
        menu_config = get_menu_config(menu_type)
        logger.info(f"Starting sheet sync process for {menu_config['name']}...")
        
        # Use menu-specific last sync file
        last_sync_file = Path(f'logs/last_sync_{menu_type}.txt')
        
        logger.info("Copying source sheet data...")
        source_data = copy_source_sheet(menu_config)
        
        target_sheet_id = get_target_sheet_id(menu_config)
        if not target_sheet_id:
            logger.info("Target sheet not found, creating new one...")
            target_sheet_id = create_target_sheet(menu_config)
        else:
            logger.info(f"Found existing target sheet: {target_sheet_id}")
        
        logger.info("Processing and updating target sheet...")
        process_and_update_sheet(source_data, target_sheet_id, menu_config)
        
        last_sync_file.parent.mkdir(parents=True, exist_ok=True)
        with open(last_sync_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        logger.info(f"Sync completed successfully for {menu_config['name']}!")
        return True
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False

def get_last_sync_time(menu_type='thca'):
    last_sync_file = Path(f'logs/last_sync_{menu_type}.txt')
    if last_sync_file.exists():
        with open(last_sync_file, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    return None