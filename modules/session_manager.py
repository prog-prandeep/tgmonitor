"""Instagram session manager module"""
import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger("ig_monitor_bot")


class SessionManager:
    """Manages Instagram session IDs"""
    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.sessions = self._load_sessions()
        self.current_index = 0
    
    def _load_sessions(self) -> List[str]:
        """Load session IDs from file"""
        if not self.session_file.exists():
            default_sessions = {
                "sessions": [
                    "session_id_1",
                    "session_id_2",
                    "session_id_3"
                ]
            }
            with open(self.session_file, 'w') as f:
                json.dump(default_sessions, f, indent=2)
            logger.warning(f"Created session.json at {self.session_file}")
            logger.warning("Please add valid Instagram session IDs!")
        
        with open(self.session_file, 'r') as f:
            data = json.load(f)
            sessions = data.get('sessions', [])
            logger.info(f"Loaded {len(sessions)} Instagram session(s)")
            return sessions
    
    def get_current_session(self) -> str:
        """Get current session ID"""
        if not self.sessions:
            raise ValueError("No Instagram sessions available!")
        return self.sessions[self.current_index]
    
    def rotate_session(self):
        """Rotate to next session"""
        self.current_index = (self.current_index + 1) % len(self.sessions)
        logger.info(f"Rotated to Instagram session {self.current_index + 1}/{len(self.sessions)}")