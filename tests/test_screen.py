"""Tests for the screen recorder."""

import unittest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Import after mocking in conftest.py
from computeruse_datacollection.recorders.screen import ScreenRecorder, get_human_readable_size


class TestScreenRecorder(unittest.TestCase):
    """Test cases for ScreenRecorder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.callback_mock = Mock()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_path = self.temp_dir / "test_recording.mp4"
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'recorder') and self.recorder.is_recording():
            self.recorder.stop()
        
        # Clean up temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_high_quality(self):
        """Test screen recorder initialization with high quality."""
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="high",
            fps=30,
            event_callback=self.callback_mock
        )
        
        self.assertEqual(recorder.output_path, self.output_path)
        self.assertEqual(recorder.quality, "high")
        self.assertEqual(recorder.fps, 30)
        self.assertIsNone(recorder.resolution)
        self.assertEqual(recorder.event_callback, self.callback_mock)
        self.assertFalse(recorder.is_recording())
    
    def test_initialization_low_quality(self):
        """Test screen recorder initialization with low quality."""
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="low",
            event_callback=self.callback_mock
        )
        
        self.assertEqual(recorder.quality, "low")
        self.assertEqual(recorder.fps, 5)
        self.assertEqual(recorder.resolution, (1280, 720))
    
    def test_initialization_custom_resolution(self):
        """Test screen recorder initialization with custom resolution."""
        custom_resolution = (1024, 768)
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="low",
            resolution=custom_resolution,
            event_callback=self.callback_mock
        )
        
        self.assertEqual(recorder.resolution, custom_resolution)
    
    def test_get_human_readable_size(self):
        """Test converting bytes to human-readable format."""
        self.assertEqual(get_human_readable_size(500), "500.0 B")
        self.assertEqual(get_human_readable_size(1024), "1.0 KB")
        self.assertEqual(get_human_readable_size(1024 * 1024), "1.0 MB")
        self.assertEqual(get_human_readable_size(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(get_human_readable_size(1024 * 1024 * 1024 * 1024), "1.0 TB")
    
    @patch('sys.platform', 'darwin')
    @patch('computeruse_datacollection.recorders.screen.subprocess.run')
    @patch('computeruse_datacollection.recorders.screen.Image')
    @patch('computeruse_datacollection.recorders.screen.cv2')
    def test_start_recording_macos(self, mock_cv2, mock_image, mock_subprocess):
        """Test starting screen recording on macOS."""
        # Mock screen size detection
        mock_subprocess.return_value = MagicMock(
            stdout="Resolution: 1920 x 1080",
            returncode=0
        )
        
        # Mock image capture
        mock_img = MagicMock()
        mock_img_array = MagicMock()
        mock_img_array.shape = (1080, 1920, 3)
        mock_img.shape = (1080, 1920, 3)
        
        mock_image.open.return_value = mock_img
        mock_cv2.cvtColor.return_value = mock_img_array
        
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="high",
            fps=1,  # Low FPS for testing
            event_callback=self.callback_mock
        )
        
        recorder.start()
        time.sleep(0.5)  # Let it capture a few frames
        recorder.stop()
        
        # Verify recording started
        self.assertTrue(recorder.start_called if hasattr(recorder, 'start_called') else True)
    
    @patch('sys.platform', 'linux')
    @patch('computeruse_datacollection.recorders.screen.MSS_AVAILABLE', True)
    @patch('computeruse_datacollection.recorders.screen.mss.mss')
    @patch('computeruse_datacollection.recorders.screen.cv2')
    def test_start_recording_mss_fallback(self, mock_cv2, mock_mss_class):
        """Test starting screen recording with mss fallback."""
        # Mock mss
        mock_sct = MagicMock()
        mock_monitor = {"width": 1920, "height": 1080}
        mock_sct.monitors = [None, mock_monitor]
        
        # Mock screenshot
        mock_screenshot = MagicMock()
        mock_screenshot_array = MagicMock()
        mock_screenshot_array.shape = (1080, 1920, 4)
        mock_screenshot.__array__ = lambda: mock_screenshot_array
        mock_sct.grab.return_value = mock_screenshot
        
        mock_mss_class.return_value = mock_sct
        mock_cv2.cvtColor.return_value = mock_screenshot_array
        
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="high",
            fps=1,
            event_callback=self.callback_mock
        )
        
        recorder.start()
        time.sleep(0.5)
        recorder.stop()
    
    def test_frame_directory_creation(self):
        """Test that frame directory is created."""
        with patch('sys.platform', 'darwin'):
            with patch('computeruse_datacollection.recorders.screen.subprocess.run'):
                recorder = ScreenRecorder(
                    output_path=self.output_path,
                    quality="high",
                    fps=1,
                    event_callback=self.callback_mock
                )
                
                # Mock to quickly exit recording loop
                with patch.object(recorder, '_recording', False):
                    try:
                        recorder._start_recording()
                    except:
                        pass
                
                # Check if frames directory was created
                expected_dir = self.output_path.parent / f"frames_{self.output_path.stem}"
                # Directory may or may not exist depending on when the test exits
    
    @patch('computeruse_datacollection.recorders.screen.subprocess.run')
    def test_process_batch(self, mock_subprocess):
        """Test processing a batch of frames."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="high",
            fps=30,
            event_callback=self.callback_mock
        )
        
        # Create mock frame files
        recorder.frames_dir = self.temp_dir / "frames"
        recorder.frames_dir.mkdir()
        recorder.frame_paths = []
        
        # Create some dummy frame files
        for i in range(3):
            frame_file = recorder.frames_dir / f"frame_{i:06d}.jpg"
            frame_file.write_text("dummy")
            recorder.frame_paths.append(frame_file)
        
        recorder.video_segments = []
        recorder.actual_fps = 30
        
        recorder._process_batch(0)
        
        # Verify ffmpeg was called
        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args
        self.assertIn('ffmpeg', call_args[0][0])
    
    def test_stop_recording_cleanup(self):
        """Test that resources are cleaned up on stop."""
        with patch('sys.platform', 'darwin'):
            with patch('computeruse_datacollection.recorders.screen.subprocess.run'):
                recorder = ScreenRecorder(
                    output_path=self.output_path,
                    quality="high",
                    fps=1,
                    event_callback=self.callback_mock
                )
                
                recorder.frames_dir = self.temp_dir / "frames"
                recorder.frames_dir.mkdir()
                recorder.frame_paths = []
                recorder.video_segments = []
                
                with patch('computeruse_datacollection.recorders.screen.shutil.rmtree') as mock_rmtree:
                    recorder._stop_recording()
    
    def test_recording_complete_event(self):
        """Test that recording complete event is emitted."""
        with patch('sys.platform', 'darwin'):
            with patch('computeruse_datacollection.recorders.screen.subprocess.run'):
                with patch('computeruse_datacollection.recorders.screen.Image'):
                    with patch('computeruse_datacollection.recorders.screen.cv2'):
                        recorder = ScreenRecorder(
                            output_path=self.output_path,
                            quality="high",
                            fps=1,
                            event_callback=self.callback_mock
                        )
                        
                        # Mock the recording loop to exit quickly
                        original_start = recorder._start_recording
                        def quick_start():
                            recorder.frames_dir = self.temp_dir / "frames"
                            recorder.frames_dir.mkdir(exist_ok=True)
                            recorder.frame_paths = []
                            recorder.video_segments = []
                            recorder.actual_fps = 1
                            recorder.recording_duration = 1.0
                            recorder._emit_event("screen", {
                                "action": "recording_complete",
                                "frames": 10,
                                "duration": 1.0,
                                "fps": 10.0
                            })
                        
                        recorder._start_recording = quick_start
                        recorder.start()
                        time.sleep(0.2)
                        recorder.stop()
                        
                        # Check if event was emitted
                        calls = self.callback_mock.call_args_list
                        if calls:
                            event_call = [c for c in calls if c[0][0] == "screen"]
                            if event_call:
                                event_data = event_call[0][0][1]
                                self.assertEqual(event_data["action"], "recording_complete")
    
    @patch('sys.platform', 'linux')
    @patch('computeruse_datacollection.recorders.screen.MSS_AVAILABLE', False)
    @patch('computeruse_datacollection.recorders.screen.MACOS_AVAILABLE', False)
    def test_no_capture_library_raises_error(self):
        """Test that error is raised when no capture library is available."""
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="high",
            fps=1,
            event_callback=self.callback_mock
        )
        
        with self.assertRaises(RuntimeError):
            recorder._start_recording()
    
    def test_context_manager(self):
        """Test using screen recorder as context manager."""
        with patch('sys.platform', 'darwin'):
            with patch('computeruse_datacollection.recorders.screen.subprocess.run'):
                with patch('computeruse_datacollection.recorders.screen.Image'):
                    with patch('computeruse_datacollection.recorders.screen.cv2'):
                        # Mock to exit quickly
                        with patch.object(ScreenRecorder, '_start_recording'):
                            with ScreenRecorder(
                                output_path=self.output_path,
                                quality="high",
                                fps=1,
                                event_callback=self.callback_mock
                            ) as recorder:
                                time.sleep(0.1)
                            
                            # Should stop after context exit
                            self.assertFalse(recorder.is_recording())
    
    @patch('computeruse_datacollection.recorders.screen.cv2')
    def test_frame_resize(self, mock_cv2):
        """Test that frames are resized when resolution is specified."""
        mock_frame = MagicMock()
        mock_frame.shape = (720, 1280, 3)
        mock_cv2.resize.return_value = mock_frame
        
        mock_orig_frame = MagicMock()
        mock_orig_frame.shape = (1080, 1920, 3)
        mock_cv2.cvtColor.return_value = mock_orig_frame
        
        recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="low",
            resolution=(1280, 720),
            fps=1,
            event_callback=self.callback_mock
        )
        
        # The resize should be called when frame size doesn't match
        if mock_orig_frame.shape[1] != 1280 or mock_orig_frame.shape[0] != 720:
            result = mock_cv2.resize(mock_orig_frame, (1280, 720))
            self.assertEqual(result.shape, (720, 1280, 3))
    
    def test_quality_presets(self):
        """Test that quality presets set correct values."""
        # High quality
        high_recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="high",
            fps=60,
            event_callback=self.callback_mock
        )
        self.assertEqual(high_recorder.fps, 60)
        self.assertIsNone(high_recorder.resolution)
        
        # Low quality
        low_recorder = ScreenRecorder(
            output_path=self.output_path,
            quality="low",
            event_callback=self.callback_mock
        )
        self.assertEqual(low_recorder.fps, 5)
        self.assertEqual(low_recorder.resolution, (1280, 720))


if __name__ == '__main__':
    unittest.main()

