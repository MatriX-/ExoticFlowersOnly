#!/usr/bin/env python3

import click
import logging
import sys
from pathlib import Path
from datetime import datetime
from src.auth import get_credentials, CREDS_PATH
from src.processor import sync_sheets, get_last_sync_time
from src.menu_configs import list_available_menus
from src.scheduler import start_scheduler, stop_scheduler_func, get_scheduler_status

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', mode='a'),
        logging.StreamHandler()
    ]
)

Path('logs').mkdir(exist_ok=True)

@click.group()
def cli():
    pass

@cli.command()
def setup():
    click.echo("Setting up Google Sheets authentication...")
    click.echo("")
    
    if not CREDS_PATH.exists():
        click.echo("  credentials.json not found!")
        click.echo("")
        click.echo("Please follow these steps:")
        click.echo("1. Go to https://console.cloud.google.com/")
        click.echo("2. Create a new project or select existing one")
        click.echo("3. Enable Google Sheets API and Google Drive API")
        click.echo("4. Create OAuth 2.0 credentials (Desktop application)")
        click.echo("5. Download credentials.json")
        click.echo(f"6. Place it in: {CREDS_PATH.absolute()}")
        return
    
    try:
        get_credentials()
        click.echo("Authentication successful!")
        click.echo("You can now use the sync command.")
    except Exception as e:
        click.echo(f"L Authentication failed: {e}")
        sys.exit(1)

@cli.command()
@click.option('--menu', '-m', type=click.Choice(['thca', 'titan', 'all']), default='thca',
              help='Which menu to sync (default: thca)')
def sync(menu):
    click.echo(f"Starting manual sync for {menu}...")
    
    if not CREDS_PATH.exists():
        click.echo("L Please run 'python main.py setup' first")
        sys.exit(1)
    
    if menu == 'all':
        # Sync all menus
        all_success = True
        for menu_type in list_available_menus():
            click.echo(f"\nSyncing {menu_type} menu...")
            success = sync_sheets(menu_type)
            if success:
                click.echo(f"✓ {menu_type} sync completed successfully!")
            else:
                click.echo(f"✗ {menu_type} sync failed. Check logs for details.")
                all_success = False
        
        if not all_success:
            sys.exit(1)
    else:
        success = sync_sheets(menu)
        if success:
            click.echo("Sync completed successfully!")
        else:
            click.echo("L Sync failed. Check logs for details.")
            sys.exit(1)

@cli.command()
@click.option('--menu', '-m', type=click.Choice(['thca', 'titan', 'all']), default='all',
              help='Which menu status to check (default: all)')
def status(menu):
    click.echo("Checking sync status...")
    click.echo("")
    
    if menu == 'all':
        for menu_type in list_available_menus():
            last_sync = get_last_sync_time(menu_type)
            if last_sync:
                click.echo(f"{menu_type.upper()} last sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                click.echo(f"{menu_type.upper()} last sync: Never")
    else:
        last_sync = get_last_sync_time(menu)
        if last_sync:
            click.echo(f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            click.echo("Last sync: Never")
    
    scheduler_status = get_scheduler_status()
    if scheduler_status['running']:
        click.echo(f"Scheduler: Running")
        if scheduler_status['next_sync']:
            next_sync = datetime.fromisoformat(scheduler_status['next_sync'])
            click.echo(f"Next sync: {next_sync.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        click.echo("Scheduler: Not running")

@cli.command(name='start-scheduler')
@click.option('--menu', '-m', type=click.Choice(['thca', 'titan', 'all']), default='all',
              help='Which menu(s) to sync on schedule (default: all)')
def start_scheduler_cmd(menu):
    click.echo(f"Starting automatic scheduler for {menu} menu(s)...")
    
    if not CREDS_PATH.exists():
        click.echo("L Please run 'python main.py setup' first")
        sys.exit(1)
    
    if start_scheduler(menu):
        click.echo(f"Scheduler started - will sync {menu} menu(s) every hour")
        click.echo("Run 'python main.py status' to check next sync time")
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            click.echo("\nStopping scheduler...")
            stop_scheduler_func()
    else:
        click.echo("Scheduler is already running")

@cli.command(name='stop-scheduler')
def stop_scheduler_cmd():
    click.echo("Stopping automatic scheduler...")
    
    if stop_scheduler_func():
        click.echo("Scheduler stopped")
    else:
        click.echo("Scheduler was not running")

if __name__ == '__main__':
    import time
    cli()