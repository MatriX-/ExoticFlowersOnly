import logging
import json
from typing import Optional, List, Any, Dict
from googleapiclient.errors import HttpError
from src.auth import get_sheets_service, get_drive_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_target_sheet_id(menu_config: dict) -> Optional[str]:
    try:
        # Try the Sheets service first since Drive API might be restricted
        sheets_service = get_sheets_service()
        
        # Check if we have a known sheet ID from previous runs
        import os
        # Use menu-specific cache file
        menu_name = menu_config.get('name', 'default').replace(' ', '_').lower()
        sheet_id_file = f'logs/target_sheet_id_{menu_name}.txt'
        if os.path.exists(sheet_id_file):
            with open(sheet_id_file, 'r') as f:
                stored_id = f.read().strip()
                # Verify this sheet still exists and has the right name
                try:
                    metadata = sheets_service.spreadsheets().get(
                        spreadsheetId=stored_id,
                        fields='properties.title'
                    ).execute()
                    if metadata['properties']['title'] == menu_config['target_sheet_name']:
                        logger.info(f"Found existing target sheet: {stored_id}")
                        return stored_id
                except HttpError:
                    # Sheet no longer exists, continue with search
                    pass
        
        # Try Drive API search as fallback
        try:
            drive_service = get_drive_service()
            results = drive_service.files().list(
                q=f"name='{menu_config['target_sheet_name']}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                sheet_id = files[0]['id']
                # Store this ID for future use
                os.makedirs('logs', exist_ok=True)
                with open(sheet_id_file, 'w') as f:
                    f.write(sheet_id)
                return sheet_id
        except HttpError as e:
            logger.warning(f"Drive API search failed: {e}")
        
        return None
    except HttpError as e:
        logger.error(f"Error searching for target sheet: {e}")
        return None

def create_target_sheet(menu_config: dict) -> str:
    try:
        sheets_service = get_sheets_service()
        spreadsheet = {
            'properties': {
                'title': menu_config['target_sheet_name']
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()
        
        sheet_id = spreadsheet.get('spreadsheetId')
        logger.info(f"Created new spreadsheet with ID: {sheet_id}")
        
        # Store the sheet ID for future updates (menu-specific)
        import os
        os.makedirs('logs', exist_ok=True)
        menu_name = menu_config.get('name', 'default').replace(' ', '_').lower()
        with open(f'logs/target_sheet_id_{menu_name}.txt', 'w') as f:
            f.write(sheet_id)
        
        return sheet_id
    except HttpError as e:
        logger.error(f"Error creating spreadsheet: {e}")
        raise

def copy_source_sheet(menu_config: dict) -> dict:
    try:
        sheets_service = get_sheets_service()
        
        # Get sheet metadata
        sheet_metadata = sheets_service.spreadsheets().get(
            spreadsheetId=menu_config['source_sheet_id']
        ).execute()
        
        source_sheet = None
        for sheet in sheet_metadata.get('sheets', []):
            if sheet['properties']['title'] == menu_config['source_sheet_tab']:
                source_sheet = sheet
                break
        
        if not source_sheet:
            raise ValueError(f"Sheet tab '{menu_config['source_sheet_tab']}' not found in source spreadsheet")
        
        # Get values first to find truncation point
        values_result = sheets_service.spreadsheets().values().get(
            spreadsheetId=menu_config['source_sheet_id'],
            range=f"{menu_config['source_sheet_tab']}!A:Z",
            valueRenderOption='FORMATTED_VALUE'
        ).execute()
        
        values = values_result.get('values', [])
        
        # Find truncation row - use markers from config
        truncate_markers = menu_config['truncate_markers']
        
        # Skip configured number of rows from the beginning
        skip_rows = menu_config.get('skip_rows', 0)
        
        truncate_row = len(values)
        found_marker = None
        
        # Start looking for truncation marker after skipped rows
        for i, row in enumerate(values):
            if i < skip_rows:
                continue
            for cell in row:
                if isinstance(cell, str):
                    cell_upper = cell.upper().strip()
                    for marker in truncate_markers:
                        if marker.upper() in cell_upper:
                            truncate_row = i
                            found_marker = marker
                            logger.info(f"Found truncation marker '{marker}' in cell '{cell}' at row {i+1}, truncating here")
                            break
                    if found_marker:
                        break
            if found_marker:
                break
        
        if not found_marker:
            logger.warning(f"No truncation marker found in {len(values)} rows, checking first few rows:")
            for i in range(min(10, len(values))):
                logger.info(f"Row {i+1}: {values[i][:3] if values[i] else 'empty'}")
            # Default truncation - let's try row 60 based on your screenshot
            truncate_row = 60
            logger.info(f"Using default truncation at row {truncate_row}")
        
        # Get full sheet data with formatting (accounting for skipped rows)
        start_row = skip_rows + 1  # +1 because sheets are 1-indexed
        sheet_data = sheets_service.spreadsheets().get(
            spreadsheetId=menu_config['source_sheet_id'],
            ranges=[f"{menu_config['source_sheet_tab']}!A{start_row}:Z{truncate_row}"],
            includeGridData=True
        ).execute()
        
        return {
            'sheet_data': sheet_data,
            'source_sheet': source_sheet,
            'values': values[skip_rows:truncate_row],
            'skip_rows': skip_rows,
            'truncate_row': truncate_row
        }
    
    except HttpError as e:
        logger.error(f"Error copying source sheet: {e}")
        raise

def process_and_update_sheet(source_data: dict, target_sheet_id: str, menu_config: dict):
    try:
        sheets_service = get_sheets_service()
        sheet_data = source_data['sheet_data']
        values = source_data['values']
        truncate_row = source_data['truncate_row']
        
        skip_rows = source_data.get('skip_rows', 0)
        actual_rows = len(values)
        logger.info(f"Processing {actual_rows} rows (skipped {skip_rows}, truncated at {truncate_row})")
        
        # Get the raw grid data to access all cell properties including hyperlinks
        source_grid_data = sheet_data['sheets'][0].get('data', [{}])[0]
        # Row data is already adjusted for skip_rows from the API call
        row_data = source_grid_data.get('rowData', [])
        
        # Discover target sheetId (do not assume 0)
        target_metadata = sheets_service.spreadsheets().get(
            spreadsheetId=target_sheet_id,
            fields='sheets(properties(sheetId,title))'
        ).execute()
        target_sheet_id_num = target_metadata['sheets'][0]['properties']['sheetId']

        # Clear target sheet completely
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=target_sheet_id,
            range='A:ZZ'
        ).execute()
        
        # Build complete cell updates including data, formatting, and hyperlinks
        requests = []
        
        # Helper: robust link extractor
        def extract_link_and_text(cell: dict):
            url = None
            
            # 1) Check chipRuns for modern UI-created hyperlinks (most common in modern sheets)
            if 'chipRuns' in cell:
                for chip_run in cell['chipRuns']:
                    chip = chip_run.get('chip', {})
                    rich_link = chip.get('richLinkProperties', {})
                    if 'uri' in rich_link:
                        url = rich_link['uri']
                        logger.debug(f"Found link in chipRuns: {url}")
                        break
            
            # 2) Entire-cell hyperlink (older format)
            if not url:
                url = cell.get('hyperlink')
                if url:
                    logger.debug(f"Found hyperlink field: {url}")
            
            # 3) Text runs
            if not url and 'textFormatRuns' in cell:
                for run in cell['textFormatRuns']:
                    link_obj = run.get('format', {}).get('link') if isinstance(run.get('format'), dict) else None
                    if link_obj and 'uri' in link_obj:
                        url = link_obj['uri']
                        logger.debug(f"Found link in textFormatRuns: {url}")
                        break
            
            # 4) Format-level link (rare but possible)
            if not url:
                user_format_link = cell.get('userEnteredFormat', {}).get('textFormat', {}).get('link', {}).get('uri')
                effective_format_link = cell.get('effectiveFormat', {}).get('textFormat', {}).get('link', {}).get('uri')
                url = user_format_link or effective_format_link
                if url:
                    logger.debug(f"Found link in format: {url}")
            
            # Display text
            text = None
            entered = cell.get('userEnteredValue') or {}
            if isinstance(entered, dict):
                # If it already is a HYPERLINK formula, preserve it entirely
                if 'formulaValue' in entered and isinstance(entered['formulaValue'], str) and entered['formulaValue'].upper().startswith('=HYPERLINK('):
                    logger.debug(f"Found existing HYPERLINK formula: {entered['formulaValue']}")
                    return None, None, entered['formulaValue']
                text = entered.get('stringValue')
            text = text or cell.get('formattedValue')
            
            # Remove file extensions from display text if present
            if url and text:
                # List of common file extensions to remove
                extensions_to_remove = ['.HEIC', '.heic', '.MOV', '.mov', '.PDF', '.pdf', 
                                      '.JPG', '.jpg', '.JPEG', '.jpeg', '.PNG', '.png',
                                      '.GIF', '.gif', '.MP4', '.mp4', '.AVI', '.avi']
                for ext in extensions_to_remove:
                    if text.endswith(ext):
                        text = text[:-len(ext)]
                        logger.debug(f"Removed extension '{ext}' from display text")
                        break
            
            if url:
                logger.info(f"Successfully extracted hyperlink: url={url}, text={text}")
            
            return url, text, None

        hyperlink_count = 0
        price_adjust_count = 0

        # Category upcharges from config
        category_upcharge = menu_config.get('category_upcharge', {})
        columns_to_remove = menu_config.get('columns_to_remove', [0, 5, 6])
        price_column = menu_config.get('price_column', 7)
        category_column = menu_config.get('category_column', 1)

        def _normalize(text: str) -> str:
            return (text or '').strip().lower()

        def _cell_plain_text(cell: dict) -> str:
            if not isinstance(cell, dict):
                return ''
            entered = cell.get('userEnteredValue') or {}
            if isinstance(entered, dict) and 'stringValue' in entered:
                return str(entered['stringValue'])
            return str(cell.get('formattedValue') or '')

        current_category = None
        
        # Helper function to check if row contains filter keywords
        def row_contains_keywords(row_values, keywords):
            """Check if any cell in row contains any of the keywords (case-insensitive)"""
            row_text = ' '.join(str(_cell_plain_text(cell)) for cell in row_values).lower()
            return any(keyword.lower() in row_text for keyword in keywords)
        
        # Check if filtering is enabled for this menu
        filter_enabled = menu_config.get('filter_enabled', False)
        filter_keywords = menu_config.get('row_filter_keywords', [])
        
        # First, create header rows with logo and contact info
        header_rows = 8  # Number of header rows to add
        
        # Add header row requests
        header_requests = []

        # Check if this is Titan menu to position header differently
        is_titan_menu = menu_config.get('name', '').lower().find('titan') != -1
        
        # Set column positions based on menu type
        if is_titan_menu:
            # For Titan: position on the left (A-E) to align with product list
            logo_start_col = 0  # A
            logo_end_col = 5    # E (exclusive)
        else:
            # For THCA and others: keep original position (D-H)
            logo_start_col = 3  # D
            logo_end_col = 8    # H (exclusive)

        # Prepare a wider canvas for the logo: merge columns and widen them
        # First, unmerge any previous header merges to keep this idempotent
        header_requests.append({
            'unmergeCells': {
                'range': {
                    'sheetId': target_sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': 2
                }
            }
        })
        header_requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': target_sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': 2,
                    'startColumnIndex': logo_start_col,
                    'endColumnIndex': logo_end_col
                },
                'mergeType': 'MERGE_ALL'
            }
        })
        # Widen columns for logo
        header_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': target_sheet_id_num,
                    'dimension': 'COLUMNS',
                    'startIndex': logo_start_col,
                    'endIndex': logo_end_col
                },
                'properties': {
                    'pixelSize': 220
                },
                'fields': 'pixelSize'
            }
        })
        
        # Row 1: Empty row for spacing
        # Row 2: Logo anchored at dynamic column position
        logo_url = "https://i.imgur.com/zCVuc8e.png"
        header_requests.append({
            'updateCells': {
                'range': {
                    'sheetId': target_sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': 2,
                    'startColumnIndex': logo_start_col,
                    'endColumnIndex': logo_start_col + 1
                },
                'rows': [{
                    'values': [{
                        'userEnteredValue': {
                            'formulaValue': f'=IMAGE("{logo_url}", 3)'
                        },
                        'userEnteredFormat': {
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'MIDDLE',
                            'backgroundColor': {'red': 0.62, 'green': 0.88, 'blue': 0.91}
                        }
                    }]
                }],
                'fields': 'userEnteredValue,userEnteredFormat'
            }
        })
        
        # Rows 3-6: Contact information centered under the logo
        contact_info = [
            {'text': '**Bulk Discounts Available**', 'bold': True},
            {'text': 'exoticflowersonly@gmail.com', 'bold': False},
            {'text': '205-974-1701', 'bold': False}
        ]
        
        for i, info in enumerate(contact_info):
            row_idx = i + 3  # Starting from row 4 (index 3)
            # Light brand blue (approximate to logo background)
            brand_blue = {'red': 0.62, 'green': 0.88, 'blue': 0.91}

            cell_format = {
                'userEnteredValue': {
                    'stringValue': info['text'].replace('**', '') if info['bold'] else info['text']
                },
                'userEnteredFormat': {
                    'horizontalAlignment': 'CENTER',
                    'verticalAlignment': 'MIDDLE',
                    'backgroundColor': brand_blue,
                    'textFormat': {
                        'bold': info['bold'],
                        'fontSize': 12 if not info['bold'] else 14
                    }
                }
            }

            # Ensure the row is merged across appropriate columns and idempotent on re-runs
            header_requests.append({
                'unmergeCells': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1
                    }
                }
            })
            header_requests.append({
                'mergeCells': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1,
                        'startColumnIndex': logo_start_col,
                        'endColumnIndex': logo_end_col
                    },
                    'mergeType': 'MERGE_ALL'
                }
            })
            
            header_requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1,
                        'startColumnIndex': logo_start_col,
                        'endColumnIndex': logo_start_col + 1
                    },
                    'rows': [{
                        'values': [cell_format]
                    }],
                    'fields': 'userEnteredValue,userEnteredFormat'
                }
            })
        
        # Add header requests to main requests list
        requests.extend(header_requests)
        
        # For Titan menu, fill header rows with brand blue only in columns A-E
        # For other menus, keep white background in non-branded areas
        if is_titan_menu:
            # Fill row 1 with brand blue (only columns A-E)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5  # Only up to column E
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.62, 'green': 0.88, 'blue': 0.91}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
            # Fill rows 3, 7, 8 with brand blue (only columns A-E)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': 2,  # Row 3 (index 2)
                        'endRowIndex': 3,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5  # Only up to column E
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.62, 'green': 0.88, 'blue': 0.91}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': 6,  # Rows 7-8 (index 6-7)
                        'endRowIndex': 8,
                        'startColumnIndex': 0,
                        'endColumnIndex': 5  # Only up to column E
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.62, 'green': 0.88, 'blue': 0.91}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
            # Fill the rest of the header rows with white (columns F onwards)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': 0,
                        'endRowIndex': header_rows,
                        'startColumnIndex': 5,  # From column F onwards
                        'endColumnIndex': 26
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
        else:
            # Original behavior for non-Titan menus
            # Part 1: rows 0..1 (exclude logo row index 1)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 26
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
            # Part 2: rows 6..header_rows (skip contact rows 3..5)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': target_sheet_id_num,
                        'startRowIndex': 6,
                        'endRowIndex': header_rows,
                        'startColumnIndex': 0,
                        'endColumnIndex': 26
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })

        # Set brand-blue background for the merged logo area
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': target_sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': 2,
                    'startColumnIndex': logo_start_col,
                    'endColumnIndex': logo_end_col
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.62, 'green': 0.88, 'blue': 0.91}
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        })
        
        # Set row height for logo row (reduce to cut whitespace)
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': target_sheet_id_num,
                    'dimension': 'ROWS',
                    'startIndex': 1,
                    'endIndex': 2
                },
                'properties': {
                    'pixelSize': 300
                },
                'fields': 'pixelSize'
            }
        })

        # Process each row up to truncation point (offset by header rows)
        target_row_index = 0  # Track target row position for filtered output
        keep_category = False  # Track if we're in a category section to keep
        current_price_category = None  # Track pricing category
        
        for row_index in range(truncate_row):  # EXPLICIT range to enforce truncation
            if row_index >= len(row_data):
                break
                
            row = row_data[row_index]
            if 'values' not in row:
                continue
            
            # Apply filtering if enabled
            if filter_enabled and filter_keywords:
                # Special case: preserve the first row after skip_rows if configured (e.g., column headers)
                preserve_header = menu_config.get('preserve_header_row', False)
                if preserve_header and row_index == 0:
                    logger.info(f"Row {row_index+1}: Preserving header row (first row after skip)")
                    # Don't apply filtering, just include this row
                    pass
                else:
                    # Check if this row is a category header (has background color, typically yellow)
                    is_category_header = False
                    if row['values'] and len(row['values']) > 0:
                        first_cell = row['values'][0]
                        if 'userEnteredFormat' in first_cell or 'effectiveFormat' in first_cell:
                            # Check for background color (category headers have colored backgrounds)
                            format_to_check = first_cell.get('userEnteredFormat') or first_cell.get('effectiveFormat', {})
                            if 'backgroundColor' in format_to_check:
                                bg_color = format_to_check['backgroundColor']
                                # Check if it has a non-white background (white is 1,1,1)
                                if bg_color and not (bg_color.get('red', 0) == 1 and bg_color.get('green', 0) == 1 and bg_color.get('blue', 0) == 1):
                                    is_category_header = True
                
                    if is_category_header:
                        # This is a category header - check if it contains our keywords
                        if row_contains_keywords(row['values'], filter_keywords):
                            keep_category = True
                            row_text = ' '.join(str(_cell_plain_text(cell)) for cell in row['values']).lower()
                            if 'indoor' in row_text:
                                current_price_category = 'indoor'
                                logger.info(f"Row {row_index+1}: Category header with 'indoor' - keeping entire section")
                            elif 'light assist' in row_text:
                                current_price_category = 'light assist'
                                logger.info(f"Row {row_index+1}: Category header with 'light assist' - keeping entire section")
                        else:
                            keep_category = False
                            current_price_category = None
                            logger.debug(f"Row {row_index+1}: Category header without keywords - skipping section")
                            continue
                    elif not keep_category:
                        # Not in a category we want to keep, skip this row
                        logger.debug(f"Row {row_index+1}: Product row in filtered section - skipping")
                        continue
                    else:
                        logger.info(f"Row {row_index+1}: Product row in kept category - including")
            
            # Set current_category for price adjustments
            current_category = current_price_category
            
            if not filter_enabled:
                # Original category detection for non-filtered menus
                target_col = 0
                if len(row['values']) > category_column:
                    type_text = _normalize(_cell_plain_text(row['values'][category_column]))
                    for cat_name in category_upcharge.keys():
                        if cat_name in type_text:
                            current_category = cat_name
                            logger.info(f"Row {row_index+1}: Detected category '{cat_name}' from TYPE column")
                            break
            
            target_col = 0

                    
            for source_col, source_cell in enumerate(row['values']):
                # Skip configured columns
                if source_col in columns_to_remove:
                    continue
                
                # Build complete cell data
                new_cell = {}

                # Helper to escape quotes for formulas
                def _escape_for_formula(text: str) -> str:
                    return text.replace('"', '""') if isinstance(text, str) else text

                # Check for hyperlinks FIRST before any other processing
                url, display_text, existing_formula = extract_link_and_text(source_cell)
                
                # Log hyperlink detection for debugging  
                if source_col == 2:  # Column C
                    logger.debug(f"Row {row_index+1}, Col C: Checking for hyperlinks in cell")
                    if url:
                        logger.info(f"Row {row_index+1}, Col C: Found hyperlink: {url}")

                # Apply category upcharge for configured price column
                # But ONLY if there's no hyperlink (hyperlinks take precedence)
                if source_col == price_column and not url and not existing_formula and 'userEnteredValue' in source_cell and isinstance(source_cell['userEnteredValue'], dict):
                    uev = source_cell['userEnteredValue']
                    base_price = None
                    if 'numberValue' in uev:
                        base_price = float(uev['numberValue'])
                    elif 'stringValue' in uev:
                        import re
                        cleaned = re.sub(r'[^0-9.\-]', '', str(uev['stringValue']))
                        try:
                            base_price = float(cleaned) if cleaned else None
                        except ValueError:
                            base_price = None
                    
                    if base_price is not None:
                        if current_category in category_upcharge:
                            upcharge = float(category_upcharge[current_category])
                            adjusted = base_price + upcharge
                            new_cell['userEnteredValue'] = {'numberValue': adjusted}
                            price_adjust_count += 1
                            logger.info(f"Row {row_index+1}: Adjusting price ${base_price} + ${upcharge} = ${adjusted} for category '{current_category}'")

                # Set the hyperlink or regular value if not already set by price adjustment
                if 'userEnteredValue' not in new_cell:
                    # We already extracted hyperlink info above
                    if existing_formula:
                        new_cell['userEnteredValue'] = {'formulaValue': existing_formula}
                        hyperlink_count += 1
                    elif url and display_text:
                        formula = f'=HYPERLINK("{_escape_for_formula(url)}","{_escape_for_formula(display_text)}")'
                        new_cell['userEnteredValue'] = {'formulaValue': formula}
                        hyperlink_count += 1
                    elif 'userEnteredValue' in source_cell:
                        # Copy regular value (text, number, formula, etc.)
                        new_cell['userEnteredValue'] = source_cell['userEnteredValue']

                # Copy formatting
                if 'userEnteredFormat' in source_cell:
                    new_cell['userEnteredFormat'] = source_cell['userEnteredFormat']
                
                # Add cell update request (offset by header rows)
                # Use target_row_index for filtered output to avoid gaps
                actual_row_index = target_row_index if filter_enabled else row_index
                requests.append({
                    'updateCells': {
                        'range': {
                            'sheetId': target_sheet_id_num,
                            'startRowIndex': actual_row_index + header_rows,
                            'endRowIndex': actual_row_index + header_rows + 1,
                            'startColumnIndex': target_col,
                            'endColumnIndex': target_col + 1
                        },
                        'rows': [{
                            'values': [new_cell]
                        }],
                        'fields': '*'  # Copy all fields
                    }
                })
                
                target_col += 1
            
            # Increment target row index after processing a kept row
            if filter_enabled:
                target_row_index += 1
        
        # Apply column widths
        if 'columnMetadata' in source_grid_data:
            col_metadata = source_grid_data['columnMetadata']
            target_col = 0
            for source_col, metadata in enumerate(col_metadata):
                # Skip configured columns
                if source_col in columns_to_remove:
                    continue
                if 'pixelSize' in metadata:
                    requests.append({
                        'updateDimensionProperties': {
                            'range': {
                                'sheetId': target_sheet_id_num,
                                'dimension': 'COLUMNS',
                                'startIndex': target_col,
                                'endIndex': target_col + 1
                            },
                            'properties': {
                                'pixelSize': metadata['pixelSize']
                            },
                            'fields': 'pixelSize'
                        }
                    })
                target_col += 1
        
        # Execute all requests in chunks with delays to avoid rate limits
        if requests:
            chunk_size = 25  # Much smaller chunks to avoid rate limits
            import time
            for i in range(0, len(requests), chunk_size):
                chunk = requests[i:i + chunk_size]
                try:
                    sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=target_sheet_id,
                        body={'requests': chunk}
                    ).execute()
                    # Add small delay between chunks to avoid rate limiting
                    if i + chunk_size < len(requests):
                        time.sleep(0.5)
                except HttpError as e:
                    if "RATE_LIMIT_EXCEEDED" in str(e):
                        logger.warning(f"Rate limit hit, waiting 30 seconds...")
                        time.sleep(30)
                        # Retry the chunk
                        sheets_service.spreadsheets().batchUpdate(
                            spreadsheetId=target_sheet_id,
                            body={'requests': chunk}
                        ).execute()
                    else:
                        raise
            logger.info(f"Applied {len(requests)} cell updates with formatting. Hyperlinks converted: {hyperlink_count}. Prices adjusted: {price_adjust_count}")
        
        logger.info(f"Successfully updated sheet: {target_sheet_id}")
        
    except HttpError as e:
        logger.error(f"Error updating target sheet: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise