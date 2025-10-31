"""Base recorder interface for all data collection recorders."""

from abc import ABC, abstractmethod
import threading
from typing import Optional, Callable, Dict, Any
from queue import Queue


class BaseRecorder(ABC):
    """Abstract base class for all recorders (keyboard, mouse, screen)."""
    
    def __init__(self, event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """Initialize the base recorder.
        
        Args:
            event_callback: Callback function to handle events (type, data)
        """
        self.event_callback = event_callback
        self._recording = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_queue: Queue = Queue()
    
    @abstractmethod
    def _start_recording(self):
        """Start the actual recording process. To be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _stop_recording(self):
        """Stop the actual recording process. To be implemented by subclasses."""
        pass
    
    def start(self):
        """Start recording in a background thread."""
        if self._recording:
            return
        
        self._recording = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._recording_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop recording and wait for thread to finish."""
        if not self._recording:
            return
        
        self._recording = False
        self._stop_event.set()
        
        # Wait for thread to finish BEFORE calling _stop_recording
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        # NOW it's safe to release resources
        self._stop_recording()
    
    def is_recording(self) -> bool:
        """Check if currently recording.
        
        Returns:
            True if recording, False otherwise
        """
        return self._recording
    
    def _recording_loop(self):
        """Main recording loop that runs in background thread."""
        try:
            self._start_recording()
        except Exception as e:
            print(f"Error in recording loop for {self.__class__.__name__}: {e}")
            self._recording = False
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event through the callback.
        
        Args:
            event_type: Type of event (keyboard, mouse, etc.)
            data: Event data dictionary
        """
        if self.event_callback:
            try:
                self.event_callback(event_type, data)
            except Exception as e:
                print(f"Error in event callback: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

