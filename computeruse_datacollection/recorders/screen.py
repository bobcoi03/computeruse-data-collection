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
import atexit
import shutil
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
        
        # Register cleanup handler to remove temp files on crash
        def cleanup_temp_files():
            """Remove temp frame directory if it still exists."""
            if self.frames_dir.exists():
                try:
                    shutil.rmtree(self.frames_dir, ignore_errors=True)
                except:
                    pass
        
        atexit.register(cleanup_temp_files)
        self._cleanup_handler = cleanup_temp_files
        
        # We'll save frames as images and use ffmpeg to create MP4
        self._video_writer = None  # Not using OpenCV VideoWriter
        self.frame_paths = []
        self.batch_size = 500  # Process frames in batches to limit memory
        self.video_segments = []  # Store paths to video segments
        
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
                
                # Process batch if we've accumulated enough frames
                if len(self.frame_paths) >= self.batch_size:
                    self._process_batch(len(self.video_segments))
                    self.frame_paths = []  # Clear for next batch
                
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
    
    def _process_batch(self, batch_index):
        """Process a batch of frames into a video segment.
        
        Args:
            batch_index: Index of this batch
        """
        if not self.frame_paths:
            return
        
        try:
            segment_path = self.frames_dir / f"segment_{batch_index:04d}.mp4"
            actual_fps = getattr(self, 'actual_fps', self.fps)
            
            # Create text file listing frames for this batch
            frames_list = self.frames_dir / f"frames_batch_{batch_index:04d}.txt"
            with open(frames_list, 'w') as f:
                for frame_path in self.frame_paths:
                    f.write(f"file '{frame_path.name}'\n")
                    f.write(f"duration {1.0/actual_fps}\n")
            
            # Use ffmpeg concat to create segment
            result = subprocess.run(
                ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(frames_list),
                 '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                 '-pix_fmt', 'yuv420p', str(segment_path), '-y'],
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0 and segment_path.exists():
                self.video_segments.append(segment_path)
                
                # Delete processed frame images to free disk space
                for frame_path in self.frame_paths:
                    try:
                        frame_path.unlink()
                    except:
                        pass
                
                # Delete frames list
                try:
                    frames_list.unlink()
                except:
                    pass
        except Exception as e:
            print(f"Warning: Failed to process batch {batch_index}: {e}")
    
    def _stop_recording(self):
        """Stop screen capture and release resources."""
        # Process any remaining frames
        if hasattr(self, 'frame_paths') and self.frame_paths:
            print(f"Processing final {len(self.frame_paths)} frames...")
            self._process_batch(len(getattr(self, 'video_segments', [])))
        
        # Combine all segments into final MP4
        if hasattr(self, 'video_segments') and self.video_segments:
            mp4_path = self.output_path.with_suffix('.mp4')
            total_segments = len(self.video_segments)
            
            print(f"Combining {total_segments} video segments...")
            
            try:
                # Create concat file for segments
                concat_file = self.frames_dir / "concat_list.txt"
                with open(concat_file, 'w') as f:
                    for segment in self.video_segments:
                        f.write(f"file '{segment.name}'\n")
                
                # Calculate dynamic timeout: 30s base + 10s per segment
                timeout = 30 + (total_segments * 10)
                
                # Concatenate all segments
                result = subprocess.run(
                    ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
                     '-c', 'copy', str(mp4_path), '-y'],
                    capture_output=True,
                    timeout=timeout
                )
                
                if result.returncode == 0 and mp4_path.exists():
                    print(f"✓ MP4 created successfully: {get_human_readable_size(mp4_path.stat().st_size)}")
                    self.output_path = mp4_path
                    
                    # Clean up segments and temp directory
                    shutil.rmtree(self.frames_dir, ignore_errors=True)
                    
                    # Unregister cleanup handler since we cleaned up successfully
                    if hasattr(self, '_cleanup_handler'):
                        try:
                            atexit.unregister(self._cleanup_handler)
                        except:
                            pass
                else:
                    print(f"Failed to create MP4")
                    if result.stderr:
                        print(f"Error: {result.stderr.decode()[:200]}")
            
            except FileNotFoundError:
                print("Error: ffmpeg not found. Install with: brew install ffmpeg")
            except subprocess.TimeoutExpired:
                print(f"Error: ffmpeg timed out after {timeout}s. Video may be too long.")
            except Exception as e:
                print(f"Error creating MP4: {e}")
        elif hasattr(self, 'frame_paths') and len(self.frame_paths) > 0:
            # Fallback: if no segments but have frames, process them
            print("No segments created, processing all frames...")
            mp4_path = self.output_path.with_suffix('.mp4')
            actual_fps = getattr(self, 'actual_fps', self.fps)
            
            # Calculate dynamic timeout based on frame count (conservative estimate)
            frame_count = len(self.frame_paths)
            timeout = max(120, frame_count // 10)  # At least 2 min, or ~0.1s per frame
            
            try:
                result = subprocess.run(
                    ['ffmpeg', '-framerate', str(actual_fps), '-i', 
                     str(self.frames_dir / 'frame_%06d.jpg'),
                     '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                     '-pix_fmt', 'yuv420p', str(mp4_path), '-y'],
                    capture_output=True,
                    timeout=timeout
                )
                
                if result.returncode == 0 and mp4_path.exists():
                    print(f"✓ MP4 created successfully: {get_human_readable_size(mp4_path.stat().st_size)}")
                    self.output_path = mp4_path
                    
                    shutil.rmtree(self.frames_dir, ignore_errors=True)
                    
                    # Unregister cleanup handler since we cleaned up successfully
                    if hasattr(self, '_cleanup_handler'):
                        try:
                            atexit.unregister(self._cleanup_handler)
                        except:
                            pass
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

