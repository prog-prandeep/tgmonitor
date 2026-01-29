"""Configuration manager module"""
import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger("ig_monitor_bot")


class Config:
    """Configuration manager"""
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.data = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            default_config = {
                "api_id": "YOUR_API_ID",
                "api_hash": "YOUR_API_HASH",
                "string_session": "YOUR_STRING_SESSION",
                "proxy_url": "http://user:pass@host:port",
                "min_check_interval": 300,
                "max_check_interval": 600,
                "generate_screenshots": True
            }
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.warning(f"Created default config.json at {self.config_path}")
            logger.warning("Please fill in your credentials and restart!")
            raise SystemExit("Configuration file created. Please fill it and restart.")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    @property
    def api_id(self) -> int:
        return int(self.data['api_id'])
    
    @property
    def api_hash(self) -> str:
        return self.data['api_hash']
    
    @property
    def string_session(self) -> str:
        return self.data['string_session']
    
    @property
    def proxy_url(self) -> str:
        return self.data['proxy_url']
    
    @property
    def min_check_interval(self) -> int:
        return self.data.get('min_check_interval', 300)
    
    @property
    def max_check_interval(self) -> int:
        return self.data.get('max_check_interval', 600)
    
    @property
    def generate_screenshots(self) -> bool:
        return self.data.get('generate_screenshots', True)