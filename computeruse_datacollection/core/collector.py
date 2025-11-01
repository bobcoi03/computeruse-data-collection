"""Main data collector orchestrator."""

from typing import Optional, Dict, Any
from pathlib import Path
import shutil
from computeruse_datacollection.core.config import Config
from computeruse_datacollection.core.session import RecordingSession
from computeruse_datacollection.recorders.keyboard import KeyboardRecorder
from computeruse_datacollection.recorders.mouse import MouseRecorder
from computeruse_datacollection.recorders.screen import ScreenRecorder
from computeruse_datacollection.recorders.audio import AudioRecorder


class DataCollector:
    """Main orchestrator for data collection."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the data collector.
        
        Args:
            config: Configuration object, or None to load from file
        """
        self.config = config or Config.load()
        self.current_session: Optional[RecordingSession] = None
        
        # Recorders
        self.keyboard_recorder: Optional[KeyboardRecorder] = None
        self.mouse_recorder: Optional[MouseRecorder] = None
        self.screen_recorder: Optional[ScreenRecorder] = None
        self.audio_recorder: Optional[AudioRecorder] = None
    
    def start_recording(self, session_name: Optional[str] = None) -> bool:
        """Start a new recording session.
        
        Args:
            session_name: Optional custom name for the session
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_recording():
            print("Recording already in progress")
            return False
        
        try:
            # Check available disk space before starting
            storage_path = self.config.get_storage_path()
            storage_path.mkdir(parents=True, exist_ok=True)
            disk_stats = shutil.disk_usage(storage_path)
            available_gb = disk_stats.free / (1024 ** 3)
            
            # Require at least 1 GB free space
            if available_gb < 1.0:
                print(f"Error: Insufficient disk space. Only {available_gb:.2f} GB available.")
                print(f"Please free up disk space or change storage location in Settings.")
                return False
            
            print(f"Available disk space: {available_gb:.1f} GB")
            
            print("Creating recording session...")
            # Create new session
            self.current_session = RecordingSession(self.config, session_name)
            self.current_session.start()
            print(f"Session created: {self.current_session.session_id}")
            
            # Start recorders based on config
            if self.config.keyboard_enabled:
                print("Starting keyboard recorder...")
                self.keyboard_recorder = KeyboardRecorder(
                    event_callback=self._handle_event
                )
                self.keyboard_recorder.start()
                print("✓ Keyboard recorder started")
            
            if self.config.mouse_enabled:
                print("Starting mouse recorder...")
                self.mouse_recorder = MouseRecorder(
                    event_callback=self._handle_event
                )
                self.mouse_recorder.start()
                print("✓ Mouse recorder started")
            
            if self.config.screen_enabled:
                print("Starting screen recorder...")
                screen_path = self.current_session.get_screen_recording_path()
                self.screen_recorder = ScreenRecorder(
                    output_path=screen_path,
                    quality=self.config.screen_quality,
                    fps=self.config.screen_fps,
                    resolution=self.config.screen_resolution,
                    event_callback=self._handle_event
                )
                self.screen_recorder.start()
                print("✓ Screen recorder started")
            
            if self.config.audio_enabled:
                print("Starting audio recorder...")
                audio_path = self.current_session.get_audio_recording_path()
                self.audio_recorder = AudioRecorder(
                    output_path=audio_path,
                    sample_rate=44100,
                    channels=2,
                    event_callback=self._handle_event
                )
                self.audio_recorder.start()
                print("✓ Audio recorder started")
            
            print(f"Recording started: {self.current_session.session_id}")
            return True
        
        except Exception as e:
            print(f"Error starting recording: {e}")
            import traceback
            traceback.print_exc()
            self.stop_recording()
            return False
    
    def stop_recording(self) -> bool:
        """Stop the current recording session.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_recording():
            print("No recording in progress")
            return False
        
        try:
            # Stop all recorders
            if self.keyboard_recorder:
                self.keyboard_recorder.stop()
                self.keyboard_recorder = None
            
            if self.mouse_recorder:
                self.mouse_recorder.stop()
                self.mouse_recorder = None
            
            if self.screen_recorder:
                self.screen_recorder.stop()
                self.screen_recorder = None
            
            if self.audio_recorder:
                self.audio_recorder.stop()
                self.audio_recorder = None
            
            # Stop session
            if self.current_session:
                self.current_session.stop()
                session_id = self.current_session.session_id
                self.current_session = None
                print(f"Recording stopped: {session_id}")
            
            return True
        
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False
    
    def is_recording(self) -> bool:
        """Check if currently recording.
        
        Returns:
            True if recording, False otherwise
        """
        return self.current_session is not None and self.current_session.is_active
    
    def get_current_session(self) -> Optional[RecordingSession]:
        """Get the current recording session.
        
        Returns:
            Current session or None
        """
        return self.current_session
    
    def _handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle events from recorders.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if self.current_session and self.current_session.is_active:
            self.current_session.record_event(event_type, data)
    
    def list_sessions(self) -> list:
        """List all recorded sessions.
        
        Returns:
            List of session IDs
        """
        from computeruse_datacollection.utils.storage import SessionStorage
        return SessionStorage.list_sessions(self.config.get_storage_path())
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Metadata dictionary or None
        """
        from computeruse_datacollection.utils.storage import SessionStorage
        return SessionStorage.get_session_metadata(session_id, self.config.get_storage_path())
    
    def get_total_storage_size(self) -> int:
        """Get total storage used by all sessions.
        
        Returns:
            Total size in bytes
        """
        from computeruse_datacollection.utils.storage import SessionStorage
        return SessionStorage.get_total_storage_size(self.config.get_storage_path())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a recorded session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            from computeruse_datacollection.utils.storage import SessionStorage
            storage = SessionStorage(session_id, self.config.get_storage_path())
            storage.delete()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

