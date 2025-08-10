# Requirements Specification

**Date:** 2025-08-08 14:00  
**Project:** Google Sheets Copy & Process Automation Tool

## Problem Statement
User needs to regularly sync a Google Sheets document they have viewer-only access to, creating and maintaining a processed copy in their own Google Drive with specific columns removed and data truncated at a specific point.

## Solution Overview
Build a Python CLI tool that:
1. Authenticates with Google Sheets API using OAuth2
2. Copies a specific Google Sheet (ID: 1ZcOCoRCaJnRA1aQZLZDFh5XozvuCRZLF_cksysep6dw, tab: THCA)
3. Processes the copy by removing columns A, F, and G
4. Truncates data at the row containing "FOR COA and MEDIA REFERENCE ONLY"
5. Saves/updates the processed sheet as "ExoticFlowersOnly Menu" in user's Drive
6. Runs automatically every hour to sync changes

## Functional Requirements

### Core Features
1. **Authentication**
   - OAuth2 flow for Google account authentication
   - Automatic token refresh and storage
   - Secure credential management

2. **Sheet Operations**
   - Copy sheet with full formatting and formulas preserved
   - Access specific sheet tab ("THCA")
   - Handle viewer-only permissions on source

3. **Data Processing**
   - Delete columns A, F, and G from the copy
   - Shift remaining columns left (no gaps)
   - Truncate data at row containing "FOR COA and MEDIA REFERENCE ONLY"
   - Preserve all formatting and formulas in retained cells

4. **Sheet Management**
   - Name processed sheet "ExoticFlowersOnly Menu"
   - Update existing sheet in place (not create new copies)
   - Maintain in user's Google Drive

5. **Automation**
   - Schedule automatic sync every 1 hour
   - Manual trigger option via CLI command
   - Show sync status and last update time

### CLI Interface
```
Commands:
- setup          : Initial OAuth setup and configuration
- sync           : Manual sync trigger
- status         : Show last sync time and next scheduled sync
- start-scheduler: Start hourly automatic sync
- stop-scheduler : Stop automatic sync
```

## Technical Requirements

### Technology Stack
- **Language:** Python 3.8+
- **Libraries:**
  - google-api-python-client (Google Sheets API)
  - google-auth-httplib2, google-auth-oauthlib (Authentication)
  - schedule or APScheduler (Scheduling)
  - click or argparse (CLI framework)

### File Structure
```
/Users/stephen/exoticflowers/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── config/
│   ├── credentials.json    # OAuth client credentials
│   └── token.pickle       # Stored auth tokens
├── src/
│   ├── auth.py           # Authentication handling
│   ├── sheets_api.py     # Google Sheets operations
│   ├── processor.py      # Sheet processing logic
│   └── scheduler.py      # Automation scheduling
└── logs/
    └── sync.log          # Operation logs
```

### Implementation Details

1. **Authentication Flow**
   - Store OAuth2 credentials in config/credentials.json
   - Save refresh tokens in config/token.pickle
   - Handle token expiration gracefully

2. **Sheet Copy Process**
   - Use sheets.spreadsheets.get() to read source
   - Create new spreadsheet or clear existing
   - Use batchUpdate to apply all changes

3. **Column Deletion**
   - Use DeleteDimensionRequest for columns 0, 5, 6 (A, F, G)
   - Apply in reverse order to maintain indices

4. **Row Truncation**
   - Search for "FOR COA and MEDIA REFERENCE ONLY" text
   - Delete all rows from that point onward
   - Use DeleteDimensionRequest with row range

5. **Scheduling**
   - Use APScheduler with BackgroundScheduler
   - Store PID for process management
   - Log all sync operations with timestamps

## Acceptance Criteria

1. ✅ User can authenticate with Google account via OAuth2
2. ✅ Tool successfully copies the specified sheet with all formatting
3. ✅ Columns A, F, and G are removed with remaining columns shifted left
4. ✅ Data is truncated at "FOR COA and MEDIA REFERENCE ONLY" row
5. ✅ Processed sheet is named "ExoticFlowersOnly Menu"
6. ✅ Existing sheet is updated in place (not duplicated)
7. ✅ Automatic sync runs every hour when scheduler is active
8. ✅ Manual sync can be triggered via CLI command
9. ✅ Authentication tokens are stored and refreshed automatically
10. ✅ Tool provides clear status messages and error handling

## Assumptions

1. User has Google account with Drive access
2. Python 3.8+ is installed on the system
3. Internet connection is available for API calls
4. Source sheet structure remains consistent (columns A, F, G exist)
5. "FOR COA and MEDIA REFERENCE ONLY" marker text remains consistent
6. User has necessary permissions to create/modify sheets in their Drive

## Next Steps

1. Set up Google Cloud Project and enable Sheets API
2. Create OAuth2 credentials and download credentials.json
3. Implement authentication module
4. Build sheet copying and processing logic
5. Add scheduling functionality
6. Create CLI interface
7. Test with actual sheet data
8. Document usage instructions

---

**Status:** Requirements Complete  
**Ready for:** Implementation