"""Audio recorder using sounddevice."""

from typing import Optional, Callable, Dict, Any
from pathlib import Path
import time
import numpy as np

try:
    import sounddevice as sd
    from scipy.io import wavfile
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

from computeruse_datacollection.recorders.base import BaseRecorder


class AudioRecorder(BaseRecorder):
    """Records system audio using sounddevice.
    
    Captures audio from the default microphone and saves as WAV file.
    """
    
    def __init__(
        self, 
        output_path: Path,
        sample_rate: int = 44100,
        channels: int = 2,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """Initialize audio recorder.
        
        Args:
            output_path: Path to save audio file
            sample_rate: Audio sample rate (Hz)
            channels: Number of audio channels (1=mono, 2=stereo)
            event_callback: Callback function to handle events
        """
        super().__init__(event_callback)
        
        if not AUDIO_AVAILABLE:
            raise ImportError(
                "Audio recording requires sounddevice and scipy. "
                "Install with: pip install sounddevice scipy"
            )
        
        self.output_path = Path(output_path)
        self.sample_rate = sample_rate
        self.channels = channels
        self._audio_data = []
        self._stream = None
    
    def _start_recording(self):
        """Start recording audio."""
        try:
            print(f"Starting audio recording...")
            print(f"  Sample rate: {self.sample_rate} Hz")
            print(f"  Channels: {self.channels}")
            print(f"  Output: {self.output_path}")
            
            # Callback for audio stream
            def audio_callback(indata, frames, time_info, status):
                """Called for each audio block."""
                if status:
                    print(f"Audio status: {status}")
                if self._recording:
                    self._audio_data.append(indata.copy())
            
            # Open audio stream
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                blocksize=4096  # Process in chunks of 4096 frames
            )
            
            self._stream.start()
            print("✓ Audio recording started")
            
            # Keep thread alive while recording
            while self._recording and not self._stop_event.is_set():
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in audio recording: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _stop_recording(self):
        """Stop recording and save audio file."""
        print("Stopping audio recording...")
        
        # Stop stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        # Save audio data
        if self._audio_data:
            try:
                print(f"Saving audio data ({len(self._audio_data)} chunks)...")
                
                # Concatenate all audio chunks
                audio_array = np.concatenate(self._audio_data, axis=0)
                
                # Ensure directory exists
                self.output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save as WAV file
                wavfile.write(
                    str(self.output_path), 
                    self.sample_rate, 
                    audio_array
                )
                
                # Get file size for display
                file_size = self.output_path.stat().st_size
                duration = len(audio_array) / self.sample_rate
                
                print(f"✓ Audio saved: {self.output_path.name}")
                print(f"  Duration: {duration:.1f}s")
                print(f"  Size: {file_size / 1024 / 1024:.1f} MB")
                
                # Emit completion event
                self._emit_event("audio", {
                    "action": "recording_stopped",
                    "duration_seconds": duration,
                    "file_size_bytes": file_size,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels
                })
                
            except Exception as e:
                print(f"Error saving audio: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("No audio data recorded")
    
    @staticmethod
    def list_devices():
        """List available audio devices.
        
        Returns:
            List of audio device information
        """
        if not AUDIO_AVAILABLE:
            return []
        
        try:
            return sd.query_devices()
        except Exception as e:
            print(f"Error listing audio devices: {e}")
            return []
    
    @staticmethod
    def get_default_device():
        """Get default input device.
        
        Returns:
            Default device info dict
        """
        if not AUDIO_AVAILABLE:
            return None
        
        try:
            return sd.query_devices(kind='input')
        except Exception as e:
            print(f"Error getting default device: {e}")
            return None

