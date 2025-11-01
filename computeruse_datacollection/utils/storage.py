"""Storage utilities for writing events and managing session data."""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import threading


class JSONLWriter:
    """Thread-safe JSONL (JSON Lines) writer for streaming event data."""
    
    def __init__(self, filepath: Path, buffer_size: int = 100):
        """Initialize the JSONL writer.
        
        Args:
            filepath: Path to the JSONL file to write to
            buffer_size: Number of events to buffer before flushing (default: 100)
        """
        self.filepath = filepath
        self.file_handle: Optional[Any] = None
        self.lock = threading.Lock()
        self.buffer = []
        self.buffer_size = buffer_size
        self.last_flush_time = time.time()
        self.flush_interval = 5.0  # Flush at least every 5 seconds
        self._open()
    
    def _open(self):
        """Open the file for writing."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = open(self.filepath, 'a', encoding='utf-8')
    
    def write_event(self, event: Dict[str, Any]):
        """Write a single event as a JSON line.
        
        Args:
            event: Dictionary containing event data
        """
        with self.lock:
            if self.file_handle:
                json_line = json.dumps(event, ensure_ascii=False)
                self.buffer.append(json_line)
                
                # Flush if buffer is full or enough time has passed
                current_time = time.time()
                if len(self.buffer) >= self.buffer_size or \
                   (current_time - self.last_flush_time) >= self.flush_interval:
                    self._flush_buffer()
                    self.last_flush_time = current_time
    
    def _flush_buffer(self):
        """Flush buffered events to disk."""
        if self.buffer and self.file_handle:
            self.file_handle.write('\n'.join(self.buffer) + '\n')
            self.file_handle.flush()
            self.buffer = []
    
    def close(self):
        """Close the file handle."""
        with self.lock:
            # Flush any remaining buffered events
            self._flush_buffer()
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class SessionStorage:
    """Manages storage for a single recording session."""
    
    def __init__(self, session_id: str, base_path: Path):
        """Initialize session storage.
        
        Args:
            session_id: Unique identifier for the session
            base_path: Base directory for all sessions
        """
        self.session_id = session_id
        self.base_path = Path(base_path).expanduser()
        self.session_dir = self.base_path / f"session_{session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.events_file = self.session_dir / "events.jsonl"
        self.metadata_file = self.session_dir / "metadata.json"
        self.screen_recording_file = self.session_dir / "screen_recording.mp4"
        self.audio_recording_file = self.session_dir / "audio_recording.wav"
        
        # JSONL writer for events
        self.events_writer: Optional[JSONLWriter] = None
    
    def start(self):
        """Start the storage session."""
        self.events_writer = JSONLWriter(self.events_file)
    
    def write_event(self, event_type: str, data: Dict[str, Any]):
        """Write an event to the JSONL file.
        
        Args:
            event_type: Type of event (keyboard, mouse, etc.)
            data: Event data dictionary
        """
        if self.events_writer:
            event = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
            self.events_writer.write_event(event)
    
    def write_metadata(self, metadata: Dict[str, Any]):
        """Write session metadata to JSON file.
        
        Args:
            metadata: Dictionary containing session metadata
        """
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def stop(self):
        """Stop the storage session and close files."""
        if self.events_writer:
            self.events_writer.close()
            self.events_writer = None
    
    def get_size(self) -> int:
        """Get total size of session directory in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.session_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def delete(self):
        """Delete the entire session directory."""
        import shutil
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)
    
    @staticmethod
    def list_sessions(base_path: Path) -> list:
        """List all session directories in the base path.
        
        Args:
            base_path: Base directory containing sessions
            
        Returns:
            List of session IDs
        """
        base_path = Path(base_path).expanduser()
        if not base_path.exists():
            return []
        
        sessions = []
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith("session_"):
                session_id = item.name.replace("session_", "")
                sessions.append(session_id)
        
        return sorted(sessions, reverse=True)  # Most recent first
    
    @staticmethod
    def get_session_metadata(session_id: str, base_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata for a specific session.
        
        Args:
            session_id: Session identifier
            base_path: Base directory containing sessions
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata_file = Path(base_path).expanduser() / f"session_{session_id}" / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def get_total_storage_size(base_path: Path) -> int:
        """Calculate total storage used by all sessions.
        
        Args:
            base_path: Base directory containing sessions
            
        Returns:
            Total size in bytes
        """
        base_path = Path(base_path).expanduser()
        if not base_path.exists():
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(base_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size

