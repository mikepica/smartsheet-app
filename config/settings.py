import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    SMARTSHEET_API_TOKEN = os.getenv('SMARTSHEET_API_TOKEN')
    WORKSPACE_ID = os.getenv('WORKSPACE_ID')
    
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / 'data'
    SHEETS_DIR = DATA_DIR / 'sheets'
    
    WORKSPACE_META_FILE = DATA_DIR / 'workspace_meta.json'
    SYNC_HISTORY_FILE = DATA_DIR / 'sync_history.json'
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = PROJECT_ROOT / 'smartsheet_sync.log'
    
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    SSL_VERIFY = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH')
    SSL_CA_BUNDLE = os.getenv('SSL_CA_BUNDLE')
    
    PROXY_HTTP = os.getenv('PROXY_HTTP')
    PROXY_HTTPS = os.getenv('PROXY_HTTPS')

    _SECURITY_MODE_ENV = os.getenv('SECURITY_MODE', 'enterprise').strip().lower()
    SECURITY_MODE = _SECURITY_MODE_ENV if _SECURITY_MODE_ENV in {'enterprise', 'testing'} else 'enterprise'

    @classmethod
    def is_testing_security_mode(cls) -> bool:
        """Return True when enterprise security should be relaxed (testing mode)"""
        return cls.SECURITY_MODE == 'testing'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.SMARTSHEET_API_TOKEN:
            raise ValueError("SMARTSHEET_API_TOKEN is required")
        
        if not cls.WORKSPACE_ID:
            raise ValueError("WORKSPACE_ID is required")
        
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_sheet_file_path(cls, sheet_id):
        """Get file path for a specific sheet"""
        return cls.SHEETS_DIR / f"sheet_{sheet_id}.json"
