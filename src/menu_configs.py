# Menu configurations for different source sheets
from datetime import datetime

# Consolidated sheet configuration
CONSOLIDATED_SHEET_CONFIG = {
    'name_template': 'Exotic Flowers Only Menu (Updated {date})',
    'cache_file': 'logs/consolidated_sheet_id.txt',
    'tabs': {
        'thca': 'THCA',
        'titan': 'Titan Botanicals'
    }
}

def get_consolidated_sheet_name():
    """Generate the consolidated sheet name with current date."""
    date_str = datetime.now().strftime("%B %-d")  # e.g., "August 21"
    return CONSOLIDATED_SHEET_CONFIG['name_template'].format(date=date_str)

MENU_CONFIGS = {
    'thca': {
        'name': 'THCA Menu',
        'source_sheet_id': '17OnrxwCf7EYjY27QM1FokRHmjkERYWSMSDg5sxscc7c',
        'source_sheet_tab': 'THCA',
        'target_sheet_name': 'Exotic Flowers Only BULK THCa Menu',
        'truncate_markers': [
            "FOR COA and MEDIA REFERENCE ONLY",
            "FOR COA AND MEDIA REFERENCE ONLY", 
            "FOR COA",
            "COA and MEDIA REFERENCE",
            "MEDIA REFERENCE ONLY"
        ],
        'skip_rows': 0,  # Number of rows to skip from the beginning
        'columns_to_remove': [0, 5, 6],  # Columns A, F, G
        'price_column': 7,  # Column index for price adjustments
        'category_column': 1,  # Column B for category detection
        'category_upcharge': {
            'indoor exotics': 75,
            'commercial ins': 150,
            'high end deps': 100,
            'standard deps': 100,
            'smalls': 125,
            'micros': 100,
            'partial pounds only left': 100,
        }
    },
    'titan': {
        'name': 'Titan Botanicals Menu',
        'source_sheet_id': '1yRDjDAtTN1i5TCt7u56FGOjNd4JplCfiUOzcbOKSQ7A',
        'source_sheet_tab': 'Sheet3',  # Default tab name, adjust if needed
        'target_sheet_name': 'Exotic Flowers Only - Titan Botanicals Menu',
        'truncate_markers': [
            "POLICIES",
            "****** POLICIES",
            "POLICIES ******"
        ],
        'skip_rows': 5,  # Skip rows 1-5
        'preserve_header_row': True,  # Keep the first row after skip_rows (row 6)
        'columns_to_remove': [],  # Don't remove any columns for Titan menu
        'price_column': 2,  # Price is in column C (index 2)
        'category_column': 1,  # Category is in column B (index 1)
        'row_filter_keywords': ['Indoor', 'Light Assist'],  # Only keep rows with these keywords
        'filter_enabled': True,  # Enable row filtering
        'category_upcharge': {
            # Simplified pricing for Indoor and Light Assist
            'indoor': 75,
            'light assist': 25,
        }
    }
}

def get_menu_config(menu_type='thca'):
    """Get configuration for a specific menu type."""
    if menu_type not in MENU_CONFIGS:
        raise ValueError(f"Unknown menu type: {menu_type}. Available: {', '.join(MENU_CONFIGS.keys())}")
    return MENU_CONFIGS[menu_type]

def list_available_menus():
    """List all available menu configurations."""
    return list(MENU_CONFIGS.keys())