"""Session management for recording sessions."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from computeruse_datacollection.utils.storage import SessionStorage
from computeruse_datacollection.core.config import Config


class RecordingSession:
    """Manages a single recording session."""
    
    def __init__(self, config: Config, session_name: Optional[str] = None):
        """Initialize a recording session.
        
        Args:
            config: Configuration object
            session_name: Optional custom name for the session
        """
        self.session_id = str(uuid.uuid4())
        self.session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config = config
        self.storage = SessionStorage(self.session_id, config.get_storage_path())
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_active = False
        
        # Metadata
        self.metadata: Dict[str, Any] = {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "recorders_enabled": {
                "keyboard": config.keyboard_enabled,
                "mouse": config.mouse_enabled,
                "screen": config.screen_enabled,
                "audio": config.audio_enabled,
            },
            "settings": {
                "screen_quality": config.screen_quality,
                "screen_fps": config.screen_fps,
                "screen_resolution": list(config.screen_resolution) if config.screen_resolution else None,
            }
        }
    
    def start(self):
        """Start the recording session."""
        self.start_time = datetime.now()
        self.is_active = True
        
        self.metadata["start_time"] = self.start_time.isoformat()
        
        # Initialize storage
        self.storage.start()
        
        # Write initial metadata
        self.storage.write_metadata(self.metadata)
    
    def stop(self):
        """Stop the recording session."""
        self.end_time = datetime.now()
        self.is_active = False
        
        # Update metadata with end time and duration
        self.metadata["end_time"] = self.end_time.isoformat()
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds()
            self.metadata["duration_seconds"] = duration
        
        # Write final metadata
        self.storage.write_metadata(self.metadata)
        
        # Stop storage
        self.storage.stop()
    
    def record_event(self, event_type: str, data: Dict[str, Any]):
        """Record an event to the session.
        
        Args:
            event_type: Type of event (keyboard, mouse, screen)
            data: Event data dictionary
        """
        if self.is_active:
            self.storage.write_event(event_type, data)
    
    def get_screen_recording_path(self) -> Path:
        """Get the path for screen recording file.
        
        Returns:
            Path to screen recording file
        """
        return self.storage.screen_recording_file
    
    def get_audio_recording_path(self) -> Path:
        """Get the path for audio recording file.
        
        Returns:
            Path to audio recording file
        """
        return self.storage.audio_recording_file
    
    def get_session_dir(self) -> Path:
        """Get the session directory path.
        
        Returns:
            Path to session directory
        """
        return self.storage.session_dir
    
    def get_duration(self) -> Optional[float]:
        """Get session duration in seconds.
        
        Returns:
            Duration in seconds or None if not ended
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None

