# Google Sheets Copy Tool - Setup Instructions

## Prerequisites
- Python 3.8 or higher
- Google account
- Internet connection

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

### Enabling APIs:
- In the Cloud Console, go to "APIs & Services" > "Library"
- Search for "Google Sheets API" and click Enable
- Search for "Google Drive API" and click Enable

## Step 3: Create OAuth 2.0 Credentials

1. In Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (app name, user support email)
   - Add your email to test users
   - You can skip optional fields
4. For Application type, choose "Desktop app"
5. Name it something like "Sheets Copy Tool"
6. Click "Create"
7. Download the credentials JSON file
8. Rename it to `credentials.json`
9. Place it in the `config/` directory of this project

## Step 4: Initial Setup

Run the setup command to authenticate:

```bash
python main.py setup
```

This will:
- Open a browser window for Google authentication
- Ask you to authorize the app
- Save authentication tokens for future use

## Step 5: Usage

### Manual Sync
To manually sync the sheet:
```bash
python main.py sync
```

### Check Status
To see the last sync time and scheduler status:
```bash
python main.py status
```

### Start Automatic Hourly Sync
To start the scheduler that syncs every hour:
```bash
python main.py start-scheduler
```
Keep this running in a terminal window, or use a process manager like `screen` or `tmux`.

### Stop Scheduler
To stop the automatic scheduler:
```bash
python main.py stop-scheduler
```

## What This Tool Does

1. **Copies** the Google Sheet with ID `1ZcOCoRCaJnRA1aQZLZDFh5XozvuCRZLF_cksysep6dw` (tab: THCA)
2. **Removes** columns A, F, and G from the copy
3. **Truncates** data at the row containing "FOR COA and MEDIA REFERENCE ONLY"
4. **Saves** the processed sheet as "ExoticFlowersOnly Menu" in your Google Drive
5. **Updates** the same sheet each time (doesn't create duplicates)
6. **Syncs** automatically every hour when scheduler is running

## Troubleshooting

### "credentials.json not found"
- Make sure you've downloaded the credentials from Google Cloud Console
- Place the file in the `config/` directory
- The file must be named exactly `credentials.json`

### Authentication errors
- Make sure you've enabled both Google Sheets API and Google Drive API
- Check that your Google account is added as a test user in the OAuth consent screen
- Try deleting `config/token.pickle` and running `python main.py setup` again

### Sheet not updating
- Check the logs in `logs/app.log` for detailed error messages
- Verify you have internet connection
- Make sure the source sheet ID and tab name haven't changed

## Running as a Background Service

For production use, consider:
- Using a process manager like `supervisor` or `systemd`
- Running in a cloud environment (Google Cloud Run, AWS Lambda, etc.)
- Setting up proper logging and monitoring

## Security Notes

- Never share your `credentials.json` or `token.pickle` files
- These files contain sensitive authentication information
- Add them to `.gitignore` if using version control