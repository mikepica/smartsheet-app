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