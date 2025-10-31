"""Screen recorder using screencapture command and opencv."""

from typing import Optional, Callable, Dict, Any, Tuple
from computeruse_datacollection.recorders.base import BaseRecorder
import cv2
import numpy as np
import time
import sys
import subprocess
import tempfile
import os
from pathlib import Path
from PIL import Image

# Check if we're on macOS
MACOS_AVAILABLE = sys.platform == 'darwin'

try:
    # Fallback to mss if not on macOS
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False


class ScreenRecorder(BaseRecorder):
    """Records screen video with configurable quality settings."""
    
    def __init__(
        self,
        output_path: Path,
        quality: str = "high",
        fps: int = 30,
        resolution: Optional[Tuple[int, int]] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """Initialize screen recorder.
        
        Args:
            output_path: Path where video file will be saved
            quality: Quality preset ("high" or "low")
            fps: Frames per second
            resolution: Target resolution (width, height), None for native
            event_callback: Callback function to handle events
        """
        super().__init__(event_callback)
        self.output_path = Path(output_path)
        self.quality = quality
        self.fps = fps
        self.resolution = resolution
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._sct: Optional[mss.mss] = None
        
        # Set quality presets
        if quality == "low":
            self.fps = 5
            self.resolution = (1280, 720) if resolution is None else resolution
        elif quality == "high":
            self.fps = fps if fps else 30
            # resolution stays None for native
    
    def _start_recording(self):
        """Start capturing screen frames."""
        # Determine if we're on macOS and use appropriate capture method
        use_macos = MACOS_AVAILABLE
        monitor = None
        
        if use_macos:
            # Get screen dimensions using system_profiler command
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Parse output for resolution (this is a simple approach)
                # Default to common resolution if parsing fails
                screen_width = 1920
                screen_height = 1080
                
                # Try to extract actual resolution
                for line in result.stdout.split('\n'):
                    if 'Resolution' in line:
                        # Format is usually like "Resolution: 1920 x 1080"
                        parts = line.split(':')
                        if len(parts) > 1:
                            dims = parts[1].strip().split('x')
                            if len(dims) >= 2:
                                try:
                                    screen_width = int(dims[0].strip())
                                    screen_height = int(dims[1].strip().split()[0])
                                    break
                                except ValueError:
                                    pass
            except Exception as e:
                print(f"Warning: Could not detect screen size, using default 1920x1080: {e}")
                screen_width = 1920
                screen_height = 1080
        elif MSS_AVAILABLE:
            # Fallback to mss
            self._sct = mss.mss()
            monitor = self._sct.monitors[1]
            screen_width = monitor["width"]
            screen_height = monitor["height"]
            use_macos = False  # Explicitly use mss
        else:
            raise RuntimeError("No screen capture library available")
        
        # Determine output resolution
        if self.resolution:
            width, height = self.resolution
        else:
            width = screen_width
            height = screen_height
        
        # Create directory to store frames temporarily
        self.frames_dir = self.output_path.parent / f"frames_{self.output_path.stem}"
        self.frames_dir.mkdir(exist_ok=True)
        
        # We'll save frames as images and use ffmpeg to create MP4
        self._video_writer = None  # Not using OpenCV VideoWriter
        self.frame_paths = []
        
        # Calculate frame interval
        frame_interval = 1.0 / self.fps
        
        # Capture loop
        frame_count = 0
        start_time = time.time()
        
        while self._recording and not self._stop_event.is_set():
            loop_start = time.time()
            
            try:
                # Capture screen based on available method
                if use_macos:
                    # Use screencapture command (more reliable)
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                        tmp_path = tmp.name
                    
                    try:
                        # Capture screen to temporary file
                        result = subprocess.run(
                            ['screencapture', '-x', '-C', tmp_path],
                            check=False,
                            capture_output=True,
                            timeout=2
                        )
                        
                        if result.returncode != 0:
                            continue
                        
                        # Check if file was created
                        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                            continue
                        
                        # Load image with PIL
                        img = Image.open(tmp_path)
                        frame = np.array(img)
                        
                        # Convert RGB to BGR for OpenCV
                        if frame.shape[2] == 3:
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        elif frame.shape[2] == 4:
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                else:
                    # Use mss fallback
                    screenshot = self._sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Resize if needed
                if self.resolution and (frame.shape[1] != width or frame.shape[0] != height):
                    frame = cv2.resize(frame, (width, height))
                
                # Write frame (with thread safety check)
                if not self._recording:
                    break
                
                # Save frame as image
                frame_filename = self.frames_dir / f"frame_{frame_count:06d}.jpg"
                cv2.imwrite(str(frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                self.frame_paths.append(frame_filename)
                frame_count += 1
                
                # Calculate how long to sleep to maintain FPS
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error capturing frame: {e}")
                break
        
        # Calculate actual capture rate
        duration = time.time() - start_time
        actual_fps = frame_count / duration if duration > 0 else self.fps
        
        # Store for use in _stop_recording
        self.actual_fps = actual_fps
        self.recording_duration = duration
        
        self._emit_event("screen", {
            "action": "recording_complete",
            "frames": frame_count,
            "duration": duration,
            "fps": actual_fps
        })
    
    def _stop_recording(self):
        """Stop screen capture and release resources."""
        # Create MP4 from saved frames using ffmpeg
        if hasattr(self, 'frame_paths') and self.frame_paths:
            mp4_path = self.output_path.with_suffix('.mp4')
            
            # Use actual capture FPS, not target FPS
            actual_fps = getattr(self, 'actual_fps', self.fps)
            print(f"Creating MP4 from {len(self.frame_paths)} frames (captured at {actual_fps:.1f} fps)...")
            
            try:
                # Use ffmpeg to create MP4 from image sequence
                # Important: use actual_fps so video duration matches recording duration
                result = subprocess.run(
                    ['ffmpeg', '-framerate', str(actual_fps), '-i', 
                     str(self.frames_dir / 'frame_%06d.jpg'),
                     '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                     '-pix_fmt', 'yuv420p', str(mp4_path), '-y'],
                    capture_output=True,
                    timeout=120
                )
                
                if result.returncode == 0 and mp4_path.exists():
                    print(f"✓ MP4 created successfully: {get_human_readable_size(mp4_path.stat().st_size)}")
                    self.output_path = mp4_path
                    
                    # Clean up frame images
                    import shutil
                    shutil.rmtree(self.frames_dir, ignore_errors=True)
                else:
                    print(f"Failed to create MP4")
                    if result.stderr:
                        print(f"Error: {result.stderr.decode()[:200]}")
            
            except FileNotFoundError:
                print("Error: ffmpeg not found. Install with: brew install ffmpeg")
            except Exception as e:
                print(f"Error creating MP4: {e}")
        
        if hasattr(self, '_sct') and self._sct:
            self._sct.close()
            self._sct = None


def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

