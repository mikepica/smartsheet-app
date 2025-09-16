import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class JSONStorage:
    def __init__(self):
        Config.validate()
        
    def save_workspace_metadata(self, workspace_data: Dict[str, Any]) -> None:
        """Save workspace metadata to JSON file"""
        try:
            with open(Config.WORKSPACE_META_FILE, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved workspace metadata to {Config.WORKSPACE_META_FILE}")
        except Exception as e:
            logger.error(f"Error saving workspace metadata: {e}")
            raise
    
    def load_workspace_metadata(self) -> Optional[Dict[str, Any]]:
        """Load workspace metadata from JSON file"""
        try:
            if Config.WORKSPACE_META_FILE.exists():
                with open(Config.WORKSPACE_META_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("Loaded workspace metadata")
                return data
            else:
                logger.info("No workspace metadata file found")
                return None
        except Exception as e:
            logger.error(f"Error loading workspace metadata: {e}")
            return None
    
    def save_sheet_data(self, sheet_id: int, sheet_data: Dict[str, Any]) -> None:
        """Save individual sheet data to JSON file"""
        try:
            file_path = Config.get_sheet_file_path(sheet_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sheet_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved sheet data to {file_path}")
        except Exception as e:
            logger.error(f"Error saving sheet {sheet_id}: {e}")
            raise
    
    def load_sheet_data(self, sheet_id: int) -> Optional[Dict[str, Any]]:
        """Load individual sheet data from JSON file"""
        try:
            file_path = Config.get_sheet_file_path(sheet_id)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded sheet data from {file_path}")
                return data
            else:
                logger.info(f"No data file found for sheet {sheet_id}")
                return None
        except Exception as e:
            logger.error(f"Error loading sheet {sheet_id}: {e}")
            return None
    
    def get_all_sheet_files(self) -> List[Path]:
        """Get list of all sheet JSON files"""
        try:
            sheet_files = list(Config.SHEETS_DIR.glob("sheet_*.json"))
            logger.info(f"Found {len(sheet_files)} sheet files")
            return sheet_files
        except Exception as e:
            logger.error(f"Error listing sheet files: {e}")
            return []
    
    def save_sync_history(self, sync_record: Dict[str, Any]) -> None:
        """Save sync operation to history"""
        try:
            history = self.load_sync_history()
            if history is None:
                history = {'sync_operations': []}
            
            sync_record['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            history['sync_operations'].append(sync_record)
            
            # Keep only last 50 sync records
            if len(history['sync_operations']) > 50:
                history['sync_operations'] = history['sync_operations'][-50:]
            
            with open(Config.SYNC_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            logger.info("Saved sync history record")
        except Exception as e:
            logger.error(f"Error saving sync history: {e}")
            raise
    
    def load_sync_history(self) -> Optional[Dict[str, Any]]:
        """Load sync history from JSON file"""
        try:
            if Config.SYNC_HISTORY_FILE.exists():
                with open(Config.SYNC_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            else:
                return None
        except Exception as e:
            logger.error(f"Error loading sync history: {e}")
            return None
    
    def get_sheet_summary(self) -> Dict[str, Any]:
        """Get summary of all stored sheet data"""
        try:
            summary = {
                'total_sheets': 0,
                'sheets': [],
                'last_updated': None,
                'total_size_mb': 0
            }
            
            sheet_files = self.get_all_sheet_files()
            summary['total_sheets'] = len(sheet_files)
            
            total_size = 0
            for file_path in sheet_files:
                try:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    # Extract sheet ID from filename
                    sheet_id = file_path.stem.replace('sheet_', '')
                    
                    # Load just metadata to get basic info
                    sheet_data = self.load_sheet_data(int(sheet_id))
                    if sheet_data and 'metadata' in sheet_data:
                        metadata = sheet_data['metadata']
                        sheet_summary = {
                            'id': sheet_id,
                            'name': metadata.get('name', 'Unknown'),
                            'last_sync': metadata.get('last_sync'),
                            'row_count': metadata.get('total_row_count', 0),
                            'size_kb': round(file_size / 1024, 2)
                        }
                        summary['sheets'].append(sheet_summary)
                        
                        # Track most recent update
                        if metadata.get('last_sync'):
                            if not summary['last_updated'] or metadata['last_sync'] > summary['last_updated']:
                                summary['last_updated'] = metadata['last_sync']
                
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
            
            summary['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            return summary
            
        except Exception as e:
            logger.error(f"Error generating sheet summary: {e}")
            return {'error': str(e)}
    
    def cleanup_old_files(self, keep_latest: int = 10) -> None:
        """Remove old sheet files, keeping only the latest ones"""
        try:
            sheet_files = self.get_all_sheet_files()
            if len(sheet_files) <= keep_latest:
                return
            
            # Sort by modification time
            sheet_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            files_to_remove = sheet_files[keep_latest:]
            for file_path in files_to_remove:
                file_path.unlink()
                logger.info(f"Removed old file: {file_path}")
            
            logger.info(f"Cleaned up {len(files_to_remove)} old files")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise