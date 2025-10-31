"""Keyboard recorder using pynput.

Note: On macOS, pynput conflicts with tkinter and must run in a separate process.
"""

from typing import Optional, Callable, Dict, Any
import time
import sys
import platform

# Platform-specific imports
if platform.system() == 'Darwin':  # macOS
    # Import in subprocess to avoid tkinter conflict
    import multiprocessing
    import queue
else:
    from pynput import keyboard

from computeruse_datacollection.recorders.base import BaseRecorder


def _keyboard_listener_process(event_queue):
    """Keyboard listener process for macOS (runs in separate process to avoid tkinter conflict).
    
    Args:
        event_queue: Multiprocessing queue to send events back to main process
    """
    from pynput import keyboard
    
    def get_key_name(key) -> str:
        """Convert pynput key to string representation."""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            elif hasattr(key, 'name'):
                return key.name
            else:
                return str(key)
        except:
            return str(key)
    
    def on_press(key):
        """Handle key press in subprocess."""
        try:
            key_name = get_key_name(key)
            event_queue.put({"key": key_name, "action": "press"})
        except:
            pass
    
    def on_release(key):
        """Handle key release in subprocess."""
        try:
            key_name = get_key_name(key)
            event_queue.put({"key": key_name, "action": "release"})
        except:
            pass
    
    # Start listener (blocks until process is terminated)
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


class KeyboardRecorder(BaseRecorder):
    """Records keyboard events (key presses and releases).
    
    On macOS, runs pynput in a separate process to avoid tkinter conflicts.
    """
    
    def __init__(self, event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """Initialize keyboard recorder.
        
        Args:
            event_callback: Callback function to handle events
        """
        super().__init__(event_callback)
        self._listener = None
        self._process = None
        self._event_queue = None
        self._is_macos = platform.system() == 'Darwin'
    
    def _start_recording(self):
        """Start listening to keyboard events."""
        if self._is_macos:
            self._start_recording_macos()
        else:
            self._start_recording_default()
    
    def _start_recording_macos(self):
        """Start keyboard recording on macOS using subprocess to avoid tkinter conflict."""
        try:
            print("Starting keyboard listener (macOS subprocess mode)...")
            import multiprocessing
            
            # Create queue for events
            self._event_queue = multiprocessing.Queue()
            
            # Start listener in separate process
            self._process = multiprocessing.Process(
                target=_keyboard_listener_process,
                args=(self._event_queue,),
                daemon=True
            )
            self._process.start()
            print("✓ Keyboard listener subprocess started")
            
            # Poll queue for events
            while self._recording and not self._stop_event.is_set():
                try:
                    # Non-blocking get with timeout
                    event_data = self._event_queue.get(timeout=0.1)
                    self._emit_event("keyboard", event_data)
                except:
                    pass  # Queue empty, continue
                    
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _start_recording_default(self):
        """Start keyboard recording on non-macOS platforms."""
        try:
            from pynput import keyboard
            print("Creating keyboard listener...")
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            print("Starting keyboard listener...")
            self._listener.start()
            print("✓ Keyboard listener started")
            
            # Keep thread alive while recording
            while self._recording and not self._stop_event.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _stop_recording(self):
        """Stop listening to keyboard events."""
        if self._is_macos and self._process:
            # Terminate subprocess
            self._process.terminate()
            self._process.join(timeout=2)
            if self._process.is_alive():
                self._process.kill()
            self._process = None
            self._event_queue = None
        elif self._listener:
            self._listener.stop()
            self._listener = None
    
    def _on_press(self, key):
        """Handle key press event.
        
        Args:
            key: Key object from pynput
        """
        if not self._recording:
            return
        
        try:
            key_name = self._get_key_name(key)
            self._emit_event("keyboard", {
                "key": key_name,
                "action": "press"
            })
        except Exception as e:
            print(f"Error handling key press: {e}")
    
    def _on_release(self, key):
        """Handle key release event.
        
        Args:
            key: Key object from pynput
        """
        if not self._recording:
            return
        
        try:
            key_name = self._get_key_name(key)
            self._emit_event("keyboard", {
                "key": key_name,
                "action": "release"
            })
        except Exception as e:
            print(f"Error handling key release: {e}")
    
    def _get_key_name(self, key) -> str:
        """Convert pynput key to string representation.
        
        Args:
            key: Key object from pynput
            
        Returns:
            String representation of the key
        """
        try:
            # Regular character key
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            # Special key
            elif hasattr(key, 'name'):
                return key.name
            else:
                return str(key)
        except:
            return str(key)

