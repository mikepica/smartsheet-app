import time
from typing import Dict, Any, List, Optional
from config.settings import Config
from src.smartsheet_client import SmartsheetClient
from src.json_storage import JSONStorage
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SyncManager:
    def __init__(self, security_mode: Optional[str] = None):
        self.smartsheet_client = SmartsheetClient(security_mode=security_mode or Config.SECURITY_MODE)
        self.security_mode = self.smartsheet_client.security_mode
        logger.info(f"SyncManager initialized with security mode: {self.security_mode}")
        self.storage = JSONStorage()
        
    def full_sync(self) -> Dict[str, Any]:
        """Perform full synchronization of all workspace data"""
        start_time = time.time()
        logger.info("Starting full workspace sync")
        
        sync_result = {
            'sync_type': 'full',
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'workspace_id': None,
            'total_sheets': 0,
            'successful_sheets': 0,
            'failed_sheets': 0,
            'errors': [],
            'duration_seconds': 0,
            'status': 'running'
        }
        
        try:
            # Get workspace information
            workspace_info = self.smartsheet_client.get_workspace_info()
            sync_result['workspace_id'] = workspace_info['id']
            
            # Save workspace metadata
            self.storage.save_workspace_metadata(workspace_info)
            
            # Get and process all sheets
            sheet_results = []
            for sheet_result in self.smartsheet_client.fetch_all_workspace_data():
                sheet_info = sheet_result['sheet_info']
                sheet_data = sheet_result['sheet_data']
                
                try:
                    # Save sheet data
                    self.storage.save_sheet_data(sheet_info['id'], sheet_data)
                    sync_result['successful_sheets'] += 1
                    
                    sheet_results.append({
                        'sheet_id': sheet_info['id'],
                        'sheet_name': sheet_info['name'],
                        'status': 'success',
                        'row_count': sheet_data['metadata']['total_row_count']
                    })
                    
                    logger.info(f"Successfully synced sheet: {sheet_info['name']}")
                    
                except Exception as e:
                    error_msg = f"Failed to save sheet {sheet_info['name']}: {e}"
                    logger.error(error_msg)
                    sync_result['failed_sheets'] += 1
                    sync_result['errors'].append(error_msg)
                    
                    sheet_results.append({
                        'sheet_id': sheet_info['id'],
                        'sheet_name': sheet_info['name'],
                        'status': 'failed',
                        'error': str(e)
                    })
            
            sync_result['total_sheets'] = sync_result['successful_sheets'] + sync_result['failed_sheets']
            sync_result['sheet_results'] = sheet_results
            sync_result['status'] = 'completed'
            
            # Calculate duration
            sync_result['duration_seconds'] = round(time.time() - start_time, 2)
            sync_result['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Save sync history
            self.storage.save_sync_history(sync_result)
            
            logger.info(f"Full sync completed. Success: {sync_result['successful_sheets']}, Failed: {sync_result['failed_sheets']}, Duration: {sync_result['duration_seconds']}s")
            
        except Exception as e:
            error_msg = f"Full sync failed: {e}"
            logger.error(error_msg)
            sync_result['status'] = 'failed'
            sync_result['errors'].append(error_msg)
            sync_result['duration_seconds'] = round(time.time() - start_time, 2)
            sync_result['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Still save the sync history for failed attempts
            self.storage.save_sync_history(sync_result)
            
        return sync_result
    
    def sync_specific_sheets(self, sheet_ids: List[int]) -> Dict[str, Any]:
        """Sync only specific sheets by their IDs"""
        start_time = time.time()
        logger.info(f"Starting sync for specific sheets: {sheet_ids}")
        
        sync_result = {
            'sync_type': 'selective',
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'requested_sheets': sheet_ids,
            'successful_sheets': 0,
            'failed_sheets': 0,
            'errors': [],
            'duration_seconds': 0,
            'status': 'running'
        }
        
        try:
            sheet_results = []
            
            for sheet_id in sheet_ids:
                try:
                    sheet_data = self.smartsheet_client.get_sheet_data(sheet_id)
                    self.storage.save_sheet_data(sheet_id, sheet_data)
                    sync_result['successful_sheets'] += 1
                    
                    sheet_results.append({
                        'sheet_id': sheet_id,
                        'sheet_name': sheet_data['metadata']['name'],
                        'status': 'success',
                        'row_count': sheet_data['metadata']['total_row_count']
                    })
                    
                    logger.info(f"Successfully synced sheet ID {sheet_id}")
                    
                except Exception as e:
                    error_msg = f"Failed to sync sheet {sheet_id}: {e}"
                    logger.error(error_msg)
                    sync_result['failed_sheets'] += 1
                    sync_result['errors'].append(error_msg)
                    
                    sheet_results.append({
                        'sheet_id': sheet_id,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            sync_result['sheet_results'] = sheet_results
            sync_result['status'] = 'completed'
            
            # Calculate duration
            sync_result['duration_seconds'] = round(time.time() - start_time, 2)
            sync_result['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Save sync history
            self.storage.save_sync_history(sync_result)
            
            logger.info(f"Selective sync completed. Success: {sync_result['successful_sheets']}, Failed: {sync_result['failed_sheets']}")
            
        except Exception as e:
            error_msg = f"Selective sync failed: {e}"
            logger.error(error_msg)
            sync_result['status'] = 'failed'
            sync_result['errors'].append(error_msg)
            sync_result['duration_seconds'] = round(time.time() - start_time, 2)
            sync_result['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            self.storage.save_sync_history(sync_result)
            
        return sync_result
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of stored data"""
        try:
            workspace_meta = self.storage.load_workspace_metadata()
            sheet_summary = self.storage.get_sheet_summary()
            sync_history = self.storage.load_sync_history()
            
            status = {
                'workspace': workspace_meta,
                'sheets_summary': sheet_summary,
                'last_sync': None,
                'total_syncs': 0
            }
            
            if sync_history and 'sync_operations' in sync_history:
                operations = sync_history['sync_operations']
                if operations:
                    status['last_sync'] = operations[-1]
                    status['total_syncs'] = len(operations)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}
    
    def validate_connection(self) -> Dict[str, Any]:
        """Validate connection to Smartsheet API"""
        try:
            logger.info("Validating Smartsheet connection")
            workspace_info = self.smartsheet_client.get_workspace_info()
            
            return {
                'status': 'success',
                'workspace_name': workspace_info['name'],
                'workspace_id': workspace_info['id'],
                'sheet_count': workspace_info['sheet_count']
            }
            
        except Exception as e:
            error_msg = f"Connection validation failed: {e}"
            logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg
            }
    
    def cleanup_old_data(self, keep_latest: int = 10) -> Dict[str, Any]:
        """Clean up old data files"""
        try:
            logger.info(f"Cleaning up old data, keeping latest {keep_latest} files")
            self.storage.cleanup_old_files(keep_latest)
            
            return {
                'status': 'success',
                'message': f'Cleanup completed, kept latest {keep_latest} files'
            }
            
        except Exception as e:
            error_msg = f"Cleanup failed: {e}"
            logger.error(error_msg)
            return {
                'status': 'failed',
                'error': error_msg
            }
