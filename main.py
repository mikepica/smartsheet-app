#!/usr/bin/env python3
"""
Smartsheet to JSON Sync Tool
Main entry point for synchronizing Smartsheet data to JSON files
"""

import sys
import argparse
import json
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.sync_manager import SyncManager
from utils.logger import setup_logger
from config.settings import Config

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Sync Smartsheet workspace data to JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py sync                    # Full sync of all sheets
  python main.py sync --sheets 123 456  # Sync specific sheet IDs
  python main.py status                  # Show current status
  python main.py validate               # Test connection
  python main.py cleanup --keep 5       # Clean up old files
        """
    )
    parser.add_argument(
        '--security-mode',
        choices=['enterprise', 'testing'],
        default=Config.SECURITY_MODE,
        help="Toggle enterprise SSL and proxy enforcement. Use 'testing' to relax checks for local testing."
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Synchronize data from Smartsheet')
    sync_parser.add_argument(
        '--sheets', 
        nargs='+', 
        type=int, 
        help='Specific sheet IDs to sync (default: all sheets)'
    )
    sync_parser.add_argument(
        '--output', 
        choices=['json', 'summary'], 
        default='summary',
        help='Output format (default: summary)'
    )
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current data status')
    status_parser.add_argument(
        '--format', 
        choices=['json', 'table'], 
        default='table',
        help='Output format (default: table)'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate Smartsheet connection')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data files')
    cleanup_parser.add_argument(
        '--keep', 
        type=int, 
        default=10,
        help='Number of latest files to keep (default: 10)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize sync manager
        sync_manager = SyncManager(security_mode=args.security_mode)
        
        if args.command == 'sync':
            handle_sync_command(sync_manager, args)
            
        elif args.command == 'status':
            handle_status_command(sync_manager, args)
            
        elif args.command == 'validate':
            handle_validate_command(sync_manager)
            
        elif args.command == 'cleanup':
            handle_cleanup_command(sync_manager, args)
            
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def handle_sync_command(sync_manager: SyncManager, args):
    """Handle sync command"""
    try:
        if args.sheets:
            print(f"Starting sync for sheets: {args.sheets}")
            result = sync_manager.sync_specific_sheets(args.sheets)
        else:
            print("Starting full workspace sync...")
            result = sync_manager.full_sync()
        
        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print_sync_summary(result)
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        print(f"Sync failed: {e}")
        sys.exit(1)

def handle_status_command(sync_manager: SyncManager, args):
    """Handle status command"""
    try:
        status = sync_manager.get_status()
        
        if args.format == 'json':
            print(json.dumps(status, indent=2))
        else:
            print_status_table(status)
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        print(f"Status check failed: {e}")
        sys.exit(1)

def handle_validate_command(sync_manager: SyncManager):
    """Handle validate command"""
    try:
        print("Validating Smartsheet connection...")
        result = sync_manager.validate_connection()
        
        if result['status'] == 'success':
            print(f"✓ Connection successful")
            print(f"  Workspace: {result['workspace_name']}")
            print(f"  ID: {result['workspace_id']}")
            print(f"  Sheets: {result['sheet_count']}")
        else:
            print(f"✗ Connection failed: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"Validation failed: {e}")
        sys.exit(1)

def handle_cleanup_command(sync_manager: SyncManager, args):
    """Handle cleanup command"""
    try:
        result = sync_manager.cleanup_old_data(args.keep)
        
        if result['status'] == 'success':
            print(f"✓ {result['message']}")
        else:
            print(f"✗ Cleanup failed: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"Cleanup failed: {e}")
        sys.exit(1)

def print_sync_summary(result):
    """Print human-readable sync summary"""
    print(f"\n{'='*50}")
    print(f"Sync Summary")
    print(f"{'='*50}")
    print(f"Type: {result['sync_type']}")
    print(f"Status: {result['status']}")
    print(f"Duration: {result['duration_seconds']}s")
    print(f"Total sheets: {result.get('total_sheets', len(result.get('sheet_results', [])))}")
    print(f"Successful: {result['successful_sheets']}")
    print(f"Failed: {result['failed_sheets']}")
    
    if result.get('sheet_results'):
        print(f"\nSheet Details:")
        for sheet in result['sheet_results']:
            status_icon = "✓" if sheet['status'] == 'success' else "✗"
            name = sheet.get('sheet_name', f"ID {sheet['sheet_id']}")
            if sheet['status'] == 'success':
                rows = sheet.get('row_count', 'Unknown')
                print(f"  {status_icon} {name} ({rows} rows)")
            else:
                print(f"  {status_icon} {name} - {sheet.get('error', 'Unknown error')}")
    
    if result.get('errors'):
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  • {error}")

def print_status_table(status):
    """Print human-readable status table"""
    print(f"\n{'='*60}")
    print(f"Smartsheet Sync Status")
    print(f"{'='*60}")
    
    if status.get('workspace'):
        ws = status['workspace']
        print(f"Workspace: {ws.get('name', 'Unknown')}")
        print(f"ID: {ws.get('id', 'Unknown')}")
        print(f"Last fetched: {ws.get('last_fetched', 'Never')}")
    
    if status.get('sheets_summary'):
        summary = status['sheets_summary']
        print(f"\nData Summary:")
        print(f"  Total sheets: {summary.get('total_sheets', 0)}")
        print(f"  Total size: {summary.get('total_size_mb', 0)} MB")
        print(f"  Last updated: {summary.get('last_updated', 'Never')}")
    
    if status.get('last_sync'):
        last_sync = status['last_sync']
        print(f"\nLast Sync:")
        print(f"  Type: {last_sync.get('sync_type', 'Unknown')}")
        print(f"  Status: {last_sync.get('status', 'Unknown')}")
        print(f"  Time: {last_sync.get('start_time', 'Unknown')}")
        print(f"  Duration: {last_sync.get('duration_seconds', 0)}s")
        print(f"  Success rate: {last_sync.get('successful_sheets', 0)}/{last_sync.get('total_sheets', 0)}")
    
    print(f"Total syncs: {status.get('total_syncs', 0)}")

if __name__ == '__main__':
    main()
