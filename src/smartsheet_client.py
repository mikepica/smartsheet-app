import smartsheet
import time
import urllib3
import ssl
import requests
from typing import List, Dict, Any, Optional, Generator
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

ALLOWED_SECURITY_MODES = {'enterprise', 'testing'}


class SmartsheetClient:
    def __init__(self, security_mode: Optional[str] = None):
        self.security_mode = self._resolve_security_mode(security_mode)
        self.client = smartsheet.Smartsheet(Config.SMARTSHEET_API_TOKEN)
        self.client.errors_as_exceptions(True)
        self._http_session: requests.Session = self._get_http_session()
        
        self._configure_ssl_and_proxy()

    def _get_http_session(self) -> requests.Session:
        """Return the underlying requests session, supporting both public and private Smartsheet attributes"""
        session = getattr(self.client, 'session', None)
        if session is None:
            session = getattr(self.client, '_session', None)
        if session is None:
            raise AttributeError("Smartsheet client does not expose an HTTP session accessor")
        return session
    
    def _serialize_value(self, value):
        """Convert Smartsheet objects to JSON-serializable values"""
        if hasattr(value, 'name'):  # EnumeratedValue objects have a 'name' attribute
            return value.name
        elif hasattr(value, '__dict__'):  # Other complex objects
            return str(value)
        else:
            return value
    
    def _resolve_security_mode(self, override: Optional[str]) -> str:
        if override:
            candidate = override.strip().lower()
            if candidate in ALLOWED_SECURITY_MODES:
                return candidate
            logger.warning(f"Unrecognized security mode '{override}', defaulting to config value")
        return Config.SECURITY_MODE
    
    def _configure_ssl_and_proxy(self):
        """Configure SSL verification and proxy settings for enterprise environments"""
        
        if self.security_mode == 'testing':
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("Enterprise SSL and proxy settings disabled (testing mode)")
            self._http_session.verify = False
            self._http_session.proxies.clear()
            return

        if not Config.SSL_VERIFY:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL verification is disabled. This is not recommended for production.")
            self._http_session.verify = False
            # Create a custom HTTPSAdapter that doesn't verify hostnames
            from requests.adapters import HTTPAdapter
            from urllib3.util.ssl_ import create_urllib3_context
            
            class NoSSLVerifyHTTPSAdapter(HTTPAdapter):
                def init_poolmanager(self, *args, **pool_kwargs):
                    context = create_urllib3_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    pool_kwargs['ssl_context'] = context
                    return super().init_poolmanager(*args, **pool_kwargs)
            
            self._http_session.mount('https://', NoSSLVerifyHTTPSAdapter())
        elif Config.SSL_CA_BUNDLE:
            logger.info(f"Using custom CA bundle: {Config.SSL_CA_BUNDLE}")
            self._http_session.verify = Config.SSL_CA_BUNDLE
        elif Config.SSL_CERT_PATH:
            logger.info(f"Using SSL certificate: {Config.SSL_CERT_PATH}")
            self._http_session.verify = Config.SSL_CERT_PATH
        
        proxies = {}
        if Config.PROXY_HTTP:
            proxies['http'] = Config.PROXY_HTTP
            logger.info(f"Using HTTP proxy: {Config.PROXY_HTTP}")
        if Config.PROXY_HTTPS:
            proxies['https'] = Config.PROXY_HTTPS
            logger.info(f"Using HTTPS proxy: {Config.PROXY_HTTPS}")
        
        if proxies:
            self._http_session.proxies.update(proxies)
        
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
                    'access_level': self._serialize_value(sheet.access_level)
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
                        'type': self._serialize_value(column.type),
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
                                'value': self._serialize_value(cell.value),
                                'display_value': self._serialize_value(cell.display_value),
                                'formula': cell.formula
                            }
                            row_data['cells'][column_id] = cell_data
                    
                    sheet_data['rows'].append(row_data)
            
            logger.info(f"Successfully fetched sheet '{sheet.name}' with {len(sheet_data['rows'])} rows")
            return sheet_data
            
        except Exception as e:
            logger.error(f"Error fetching sheet {sheet_id}: {e}")
            raise

    def fetch_all_workspace_data(self) -> Generator[Dict[str, Any], None, None]:
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
