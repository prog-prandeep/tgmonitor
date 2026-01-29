"""Data manager module for monitored accounts"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("ig_monitor_bot")


class DataManager:
    """Manages monitored accounts database"""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load monitored accounts from file"""
        if not self.file_path.exists():
            return {}
        
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {}
    
    def _save_data(self):
        """Save monitored accounts to file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def add_account(self, username: str, chat_id: int):
        """Add account to monitoring"""
        self.data[username.lower()] = {
            "username": username,
            "chat_id": chat_id,
            "added_at": datetime.now().isoformat()
        }
        self._save_data()
        logger.info(f"Added @{username} to database")
    
    def remove_account(self, username: str) -> bool:
        """Remove account from monitoring"""
        username = username.lower()
        if username in self.data:
            del self.data[username]
            self._save_data()
            logger.info(f"Removed @{username} from database")
            return True
        return False
    
    def is_monitoring(self, username: str) -> bool:
        """Check if account is being monitored"""
        return username.lower() in self.data
    
    def get_account(self, username: str) -> Optional[Dict]:
        """Get account info"""
        return self.data.get(username.lower())
    
    def get_all_accounts(self) -> Dict:
        """Get all monitored accounts"""
        return self.data
    
    def clear_all(self):
        """Clear all monitored accounts"""
        count = len(self.data)
        self.data = {}
        self._save_data()
        logger.info(f"Cleared all {count} accounts from database")