"""Mouse recorder using pynput.

Note: On macOS, pynput conflicts with tkinter and must run in a separate process.
"""

from typing import Optional, Callable, Dict, Any
import time
import platform

# Platform-specific imports
if platform.system() == 'Darwin':  # macOS
    # Import in subprocess to avoid tkinter conflict
    import multiprocessing
    import queue
else:
    from pynput import mouse

from computeruse_datacollection.recorders.base import BaseRecorder


def _mouse_listener_process(event_queue):
    """Mouse listener process for macOS (runs in separate process to avoid tkinter conflict).
    
    Args:
        event_queue: Multiprocessing queue to send events back to main process
    """
    from pynput import mouse
    
    def get_button_name(button) -> str:
        """Convert pynput button to string representation."""
        try:
            if hasattr(button, 'name'):
                return button.name
            else:
                return str(button)
        except:
            return str(button)
    
    def on_move(x, y):
        """Handle mouse move in subprocess."""
        try:
            # Use put_nowait to avoid blocking if queue is full
            event_queue.put_nowait({"x": int(x), "y": int(y), "action": "move"})
        except:
            pass  # Queue full or other error, skip this event
    
    def on_click(x, y, button, pressed):
        """Handle mouse click in subprocess."""
        try:
            button_name = get_button_name(button)
            action = "press" if pressed else "release"
            event_queue.put_nowait({
                "x": int(x), 
                "y": int(y), 
                "button": button_name, 
                "action": action
            })
        except:
            pass  # Queue full or other error, skip this event
    
    def on_scroll(x, y, dx, dy):
        """Handle mouse scroll in subprocess."""
        try:
            event_queue.put_nowait({
                "x": int(x), 
                "y": int(y), 
                "dx": int(dx), 
                "dy": int(dy), 
                "action": "scroll"
            })
        except:
            pass  # Queue full or other error, skip this event
    
    # Start listener (blocks until process is terminated)
    with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()


class MouseRecorder(BaseRecorder):
    """Records mouse events (movement, clicks, scrolls).
    
    On macOS, runs pynput in a separate process to avoid tkinter conflicts.
    """
    
    def __init__(self, event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """Initialize mouse recorder.
        
        Args:
            event_callback: Callback function to handle events
        """
        super().__init__(event_callback)
        self._listener = None
        self._process = None
        self._event_queue = None
        self._is_macos = platform.system() == 'Darwin'
    
    def _start_recording(self):
        """Start listening to mouse events."""
        if self._is_macos:
            self._start_recording_macos()
        else:
            self._start_recording_default()
    
    def _start_recording_macos(self):
        """Start mouse recording on macOS using subprocess to avoid tkinter conflict."""
        try:
            print("Starting mouse listener (macOS subprocess mode)...")
            import multiprocessing
            
            # Create queue for events with maxsize to prevent unbounded growth
            # 10000 events = ~100 seconds of mouse movement at 100 events/sec
            self._event_queue = multiprocessing.Queue(maxsize=10000)
            
            # Start listener in separate process
            self._process = multiprocessing.Process(
                target=_mouse_listener_process,
                args=(self._event_queue,),
                daemon=True
            )
            self._process.start()
            print("✓ Mouse listener subprocess started")
            
            # Poll queue for events
            last_health_check = time.time()
            while self._recording and not self._stop_event.is_set():
                try:
                    # Non-blocking get with timeout
                    event_data = self._event_queue.get(timeout=0.1)
                    self._emit_event("mouse", event_data)
                except:
                    pass  # Queue empty, continue
                
                # Periodically check if subprocess is still alive (every 5 seconds)
                if time.time() - last_health_check > 5.0:
                    if not self._process.is_alive():
                        print("⚠ Warning: Mouse subprocess died unexpectedly")
                        self._recording = False
                        break
                    last_health_check = time.time()
                    
        except Exception as e:
            print(f"Error in mouse listener: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _start_recording_default(self):
        """Start mouse recording on non-macOS platforms."""
        try:
            from pynput import mouse
            print("Creating mouse listener...")
            self._listener = mouse.Listener(
                on_move=self._on_move,
                on_click=self._on_click,
                on_scroll=self._on_scroll
            )
            print("Starting mouse listener...")
            self._listener.start()
            print("✓ Mouse listener started")
            
            # Keep thread alive while recording
            while self._recording and not self._stop_event.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in mouse listener: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _stop_recording(self):
        """Stop listening to mouse events."""
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
    
    def _on_move(self, x, y):
        """Handle mouse move event.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        if not self._recording:
            return
        
        try:
            self._emit_event("mouse", {
                "x": int(x),
                "y": int(y),
                "action": "move"
            })
        except Exception as e:
            print(f"Error handling mouse move: {e}")
    
    def _on_click(self, x, y, button, pressed):
        """Handle mouse click event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            pressed: True if pressed, False if released
        """
        if not self._recording:
            return
        
        try:
            button_name = self._get_button_name(button)
            action = "press" if pressed else "release"
            
            self._emit_event("mouse", {
                "x": int(x),
                "y": int(y),
                "button": button_name,
                "action": action
            })
        except Exception as e:
            print(f"Error handling mouse click: {e}")
    
    def _on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            dx: Horizontal scroll amount
            dy: Vertical scroll amount
        """
        if not self._recording:
            return
        
        try:
            self._emit_event("mouse", {
                "x": int(x),
                "y": int(y),
                "dx": int(dx),
                "dy": int(dy),
                "action": "scroll"
            })
        except Exception as e:
            print(f"Error handling mouse scroll: {e}")
    
    def _get_button_name(self, button) -> str:
        """Convert pynput button to string representation.
        
        Args:
            button: Button object from pynput
            
        Returns:
            String representation of the button
        """
        try:
            if hasattr(button, 'name'):
                return button.name
            else:
                return str(button)
        except:
            return str(button)

