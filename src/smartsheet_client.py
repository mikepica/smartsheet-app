import smartsheet
import time
from typing import List, Dict, Any, Optional
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SmartsheetClient:
    def __init__(self):
        self.client = smartsheet.Smartsheet(Config.SMARTSHEET_API_TOKEN)
        self.client.errors_as_exceptions(True)
        
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get workspace information and metadata"""
        try:
            workspace = self.client.Workspaces.get_workspace(Config.WORKSPACE_ID)
            logger.info(f"Retrieved workspace: {workspace.name}")
            
            return {
                'id': workspace.id,
                'name': workspace.name,
                'permalink': workspace.permalink,
                'last_fetched': time.strftime('%Y-%m-%d %H:%M:%S'),
                'sheet_count': len(workspace.sheets) if workspace.sheets else 0
            }
        except Exception as e:
            logger.error(f"Error fetching workspace info: {e}")
            raise
    
    def get_all_sheets_in_workspace(self) -> List[Dict[str, Any]]:
        """Get list of all sheets in the workspace"""
        try:
            workspace = self.client.Workspaces.get_workspace(
                Config.WORKSPACE_ID, 
                include='sheets'
            )
            
            if not workspace.sheets:
                logger.warning("No sheets found in workspace")
                return []
            
            sheets_info = []
            for sheet in workspace.sheets:
                sheet_info = {
                    'id': sheet.id,
                    'name': sheet.name,
                    'permalink': sheet.permalink,
                    'created_at': sheet.created_at.isoformat() if sheet.created_at else None,
                    'modified_at': sheet.modified_at.isoformat() if sheet.modified_at else None,
                    'access_level': sheet.access_level
                }
                sheets_info.append(sheet_info)
            
            logger.info(f"Found {len(sheets_info)} sheets in workspace")
            return sheets_info
            
        except Exception as e:
            logger.error(f"Error fetching sheets list: {e}")
            raise
    
    def get_sheet_data(self, sheet_id: int) -> Dict[str, Any]:
        """Get complete data for a specific sheet"""
        try:
            logger.info(f"Fetching data for sheet ID: {sheet_id}")
            
            sheet = self.client.Sheets.get_sheet(sheet_id)
            
            sheet_data = {
                'metadata': {
                    'id': sheet.id,
                    'name': sheet.name,
                    'permalink': sheet.permalink,
                    'version': sheet.version,
                    'total_row_count': sheet.total_row_count,
                    'created_at': sheet.created_at.isoformat() if sheet.created_at else None,
                    'modified_at': sheet.modified_at.isoformat() if sheet.modified_at else None,
                    'last_sync': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'columns': [],
                'rows': []
            }
            
            if sheet.columns:
                for column in sheet.columns:
                    column_data = {
                        'id': column.id,
                        'title': column.title,
                        'type': column.type,
                        'primary': column.primary,
                        'index': column.index,
                        'width': column.width,
                        'locked': column.locked
                    }
                    sheet_data['columns'].append(column_data)
            
            if sheet.rows:
                for row in sheet.rows:
                    row_data = {
                        'id': row.id,
                        'row_number': row.row_number,
                        'parent_id': row.parent_id,
                        'version': row.version,
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'modified_at': row.modified_at.isoformat() if row.modified_at else None,
                        'cells': {}
                    }
                    
                    if row.cells:
                        for cell in row.cells:
                            column_id = str(cell.column_id)
                            cell_data = {
                                'value': cell.value,
                                'display_value': cell.display_value,
                                'formula': cell.formula
                            }
                            row_data['cells'][column_id] = cell_data
                    
                    sheet_data['rows'].append(row_data)
            
            logger.info(f"Successfully fetched sheet '{sheet.name}' with {len(sheet_data['rows'])} rows")
            return sheet_data
            
        except Exception as e:
            logger.error(f"Error fetching sheet {sheet_id}: {e}")
            raise
    
    def fetch_all_workspace_data(self) -> Dict[str, Any]:
        """Fetch all data from workspace including metadata and all sheets"""
        try:
            logger.info("Starting full workspace data fetch")
            
            workspace_info = self.get_workspace_info()
            sheets_list = self.get_all_sheets_in_workspace()
            
            all_data = {
                'workspace': workspace_info,
                'sheets_metadata': sheets_list,
                'fetch_summary': {
                    'total_sheets': len(sheets_list),
                    'successful_fetches': 0,
                    'failed_fetches': 0,
                    'errors': []
                }
            }
            
            for sheet_info in sheets_list:
                try:
                    sheet_data = self.get_sheet_data(sheet_info['id'])
                    all_data['fetch_summary']['successful_fetches'] += 1
                    
                    yield {
                        'sheet_info': sheet_info,
                        'sheet_data': sheet_data
                    }
                    
                except Exception as e:
                    error_msg = f"Failed to fetch sheet {sheet_info['name']} (ID: {sheet_info['id']}): {e}"
                    logger.error(error_msg)
                    all_data['fetch_summary']['failed_fetches'] += 1
                    all_data['fetch_summary']['errors'].append(error_msg)
                    continue
            
            logger.info(f"Workspace fetch complete. Success: {all_data['fetch_summary']['successful_fetches']}, Failed: {all_data['fetch_summary']['failed_fetches']}")
            
        except Exception as e:
            logger.error(f"Error in full workspace fetch: {e}")
            raise