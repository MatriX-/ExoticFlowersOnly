### Exotic Flowers – Google Sheets Copy Tool

Automates copying and transforming a source Google Sheet into a branded target sheet on your Google Drive, with link preservation, header branding, and category-based price adjustments. Includes a CLI and an hourly scheduler.

### Features
- Copies a specific source sheet/tab and writes to a single target sheet (no duplicates)
- Removes columns A, F, and G from the copy
- Truncates rows at a marker (default: "FOR COA and MEDIA REFERENCE ONLY")
- Preserves hyperlinks and converts them to HYPERLINK formulas
- Adds a branded header (logo + contact info)
- Applies category-based upcharges to price column
- Optional hourly sync via built-in scheduler

### Requirements
- Python 3.8+
- Google Cloud project with:
  - Google Sheets API enabled
  - Google Drive API enabled

### Quickstart
1) Install dependencies

```bash
pip install -r requirements.txt
```

2) Create OAuth credentials and place the file
- In Google Cloud Console, create OAuth 2.0 credentials (Desktop app)
- Download and rename to `credentials.json`
- Put it in the `config/` directory

3) Authenticate

```bash
python main.py setup
```

4) Run a manual sync

```bash
python main.py sync
```

5) Start hourly scheduler (optional)

```bash
python main.py start-scheduler
```

Check status:

```bash
python main.py status
```

Stop scheduler:

```bash
python main.py stop-scheduler
```

### Configuration
- Source/target behavior and labels are defined in `src/sheets_api.py`:
  - `SOURCE_SHEET_ID`: Source spreadsheet ID
  - `SOURCE_SHEET_TAB`: Tab name to read (default: `THCA`)
  - `TARGET_SHEET_NAME`: Target spreadsheet title
  - `TRUNCATE_MARKER`: Text used to determine where to stop copying
  - Category upcharges: see `process_and_update_sheet()` mapping

### Logs & State
- Logs: `logs/app.log`
- Last sync time: `logs/last_sync.txt`
- Target sheet id cache: `logs/target_sheet_id.txt`
- Scheduler PID: `logs/scheduler.pid`

### Security
- Do not commit `config/credentials.json` or `config/token.pickle`.
- These are already ignored by `.gitignore`.

### CLI Reference
Implemented in `main.py` using Click:
- `python main.py setup` – Perform Google OAuth and cache token
- `python main.py sync` – One-off sync run
- `python main.py status` – Show last sync and scheduler status
- `python main.py start-scheduler` – Begin hourly sync loop
- `python main.py stop-scheduler` – Stop scheduler

### Development
- Main modules:
  - `src/auth.py` – OAuth and Google API service creation
  - `src/processor.py` – High-level sync orchestration
  - `src/scheduler.py` – Hourly scheduler
  - `src/sheets_api.py` – Google Sheets/Drive operations and transformations

### Troubleshooting
- "credentials.json not found": place it in `config/credentials.json`
- Authentication issues: ensure both Sheets and Drive APIs are enabled and your account is a test user
- No updates: inspect `logs/app.log` and verify the source sheet/tab and truncate marker

### License
Proprietary – internal use for Exotic Flowers.


