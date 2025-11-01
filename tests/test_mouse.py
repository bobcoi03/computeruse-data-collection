"""Tests for the mouse recorder."""

import unittest
import time
import platform
from unittest.mock import Mock, patch, MagicMock
from computeruse_datacollection.recorders.mouse import MouseRecorder


class MockButton:
    """Mock pynput button object."""
    def __init__(self, name):
        self.name = name


class TestMouseRecorder(unittest.TestCase):
    """Test cases for MouseRecorder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.callback_mock = Mock()
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'recorder') and self.recorder.is_recording():
            self.recorder.stop()
    
    def test_initialization(self):
        """Test mouse recorder initialization."""
        recorder = MouseRecorder(event_callback=self.callback_mock)
        
        self.assertFalse(recorder.is_recording())
        self.assertEqual(recorder.event_callback, self.callback_mock)
        self.assertIsNone(recorder._listener)
        self.assertIsNone(recorder._process)
        self.assertIsNone(recorder._event_queue)
        self.assertEqual(recorder._is_macos, platform.system() == 'Darwin')
    
    def test_get_button_name(self):
        """Test getting button name."""
        recorder = MouseRecorder()
        button = MockButton('left')
        
        button_name = recorder._get_button_name(button)
        self.assertEqual(button_name, 'left')
    
    def test_get_button_name_fallback(self):
        """Test getting button name for unknown buttons."""
        recorder = MouseRecorder()
        button = "unknown_button"
        
        button_name = recorder._get_button_name(button)
        self.assertEqual(button_name, str(button))
    
    @patch('platform.system')
    @patch('pynput.mouse')
    def test_start_recording_non_macos(self, mock_mouse, mock_platform):
        """Test starting mouse recording on non-macOS platforms."""
        mock_platform.return_value = 'Linux'
        mock_listener = MagicMock()
        mock_mouse.Listener.return_value = mock_listener
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder.start()
        time.sleep(0.2)
        
        # Verify listener was created and started
        mock_mouse.Listener.assert_called_once()
        mock_listener.start.assert_called_once()
        self.assertTrue(recorder.is_recording())
        
        recorder.stop()
        time.sleep(0.1)
        mock_listener.stop.assert_called_once()
    
    @patch('platform.system')
    def test_on_move_event(self, mock_platform):
        """Test handling mouse move events."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        recorder._on_move(100, 200)
        
        # Verify event was emitted
        self.callback_mock.assert_called_once()
        call_args = self.callback_mock.call_args
        self.assertEqual(call_args[0][0], "mouse")
        self.assertEqual(call_args[0][1]["x"], 100)
        self.assertEqual(call_args[0][1]["y"], 200)
        self.assertEqual(call_args[0][1]["action"], "move")
    
    @patch('platform.system')
    def test_on_click_press_event(self, mock_platform):
        """Test handling mouse click press events."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        button = MockButton('left')
        recorder._on_click(150, 250, button, True)
        
        # Verify event was emitted
        self.callback_mock.assert_called_once()
        call_args = self.callback_mock.call_args
        self.assertEqual(call_args[0][0], "mouse")
        self.assertEqual(call_args[0][1]["x"], 150)
        self.assertEqual(call_args[0][1]["y"], 250)
        self.assertEqual(call_args[0][1]["button"], "left")
        self.assertEqual(call_args[0][1]["action"], "press")
    
    @patch('platform.system')
    def test_on_click_release_event(self, mock_platform):
        """Test handling mouse click release events."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        button = MockButton('right')
        recorder._on_click(175, 275, button, False)
        
        # Verify event was emitted
        self.callback_mock.assert_called_once()
        call_args = self.callback_mock.call_args
        self.assertEqual(call_args[0][0], "mouse")
        self.assertEqual(call_args[0][1]["x"], 175)
        self.assertEqual(call_args[0][1]["y"], 275)
        self.assertEqual(call_args[0][1]["button"], "right")
        self.assertEqual(call_args[0][1]["action"], "release")
    
    @patch('platform.system')
    def test_on_scroll_event(self, mock_platform):
        """Test handling mouse scroll events."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        recorder._on_scroll(300, 400, 0, 5)
        
        # Verify event was emitted
        self.callback_mock.assert_called_once()
        call_args = self.callback_mock.call_args
        self.assertEqual(call_args[0][0], "mouse")
        self.assertEqual(call_args[0][1]["x"], 300)
        self.assertEqual(call_args[0][1]["y"], 400)
        self.assertEqual(call_args[0][1]["dx"], 0)
        self.assertEqual(call_args[0][1]["dy"], 5)
        self.assertEqual(call_args[0][1]["action"], "scroll")
    
    @patch('platform.system')
    def test_event_not_emitted_when_not_recording(self, mock_platform):
        """Test that events are not emitted when not recording."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = False
        
        recorder._on_move(10, 20)
        recorder._on_click(10, 20, MockButton('left'), True)
        recorder._on_scroll(10, 20, 0, 1)
        
        # No events should be emitted
        self.callback_mock.assert_not_called()
    
    @patch('platform.system')
    def test_event_handler_error_handling(self, mock_platform):
        """Test that errors in event handlers are caught."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        # Make callback raise an error
        self.callback_mock.side_effect = Exception("Test error")
        
        # Should not raise exception
        with patch('builtins.print'):
            recorder._on_move(50, 60)  # Should handle error gracefully
    
    @patch('platform.system')
    def test_coordinate_conversion_to_int(self, mock_platform):
        """Test that coordinates are converted to integers."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        # Pass float coordinates
        recorder._on_move(100.7, 200.3)
        
        # Verify coordinates were converted to int
        call_args = self.callback_mock.call_args
        self.assertIsInstance(call_args[0][1]["x"], int)
        self.assertIsInstance(call_args[0][1]["y"], int)
        self.assertEqual(call_args[0][1]["x"], 100)
        self.assertEqual(call_args[0][1]["y"], 200)
    
    @patch('platform.system')
    @patch('multiprocessing.Queue')
    @patch('multiprocessing.Process')
    def test_start_recording_macos(self, mock_process_class, mock_queue_class, mock_platform):
        """Test starting mouse recording on macOS."""
        mock_platform.return_value = 'Darwin'
        mock_queue = MagicMock()
        mock_process = MagicMock()
        mock_process.is_alive.return_value = True
        
        mock_queue_class.return_value = mock_queue
        mock_process_class.return_value = mock_process
        
        # Mock queue to return empty (timeout)
        mock_queue.get.side_effect = Exception("Empty")
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = True
        recorder.start()
        time.sleep(0.2)
        
        # Verify process was created and started
        mock_queue_class.assert_called_once()
        mock_process_class.assert_called_once()
        mock_process.start.assert_called_once()
        
        recorder.stop()
        time.sleep(0.1)
        mock_process.terminate.assert_called_once()
    
    @patch('platform.system')
    @patch('computeruse_datacollection.recorders.mouse.multiprocessing')
    def test_macos_event_queue_processing(self, mock_multiprocessing, mock_platform):
        """Test that macOS subprocess events are processed correctly."""
        mock_platform.return_value = 'Darwin'
        mock_queue = MagicMock()
        mock_process = MagicMock()
        mock_process.is_alive.return_value = True
        
        # Simulate queue returning events then timing out
        mock_queue.get.side_effect = [
            {"x": 100, "y": 200, "action": "move"},
            {"x": 150, "y": 250, "button": "left", "action": "press"},
            {"x": 200, "y": 300, "dx": 0, "dy": 5, "action": "scroll"},
            Exception("Empty")
        ]
        
        mock_multiprocessing.Queue.return_value = mock_queue
        mock_multiprocessing.Process.return_value = mock_process
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = True
        recorder.start()
        time.sleep(0.3)
        
        # Check that events were processed
        calls = self.callback_mock.call_args_list
        if len(calls) >= 3:
            # Move event
            self.assertEqual(calls[0][0][0], "mouse")
            self.assertEqual(calls[0][0][1]["action"], "move")
            
            # Click event
            self.assertEqual(calls[1][0][0], "mouse")
            self.assertEqual(calls[1][0][1]["action"], "press")
            
            # Scroll event
            self.assertEqual(calls[2][0][0], "mouse")
            self.assertEqual(calls[2][0][1]["action"], "scroll")
        
        recorder.stop()
    
    @patch('platform.system')
    @patch('computeruse_datacollection.recorders.mouse.multiprocessing')
    def test_macos_subprocess_health_check(self, mock_multiprocessing, mock_platform):
        """Test that macOS subprocess health is monitored."""
        mock_platform.return_value = 'Darwin'
        mock_queue = MagicMock()
        mock_process = MagicMock()
        
        # Simulate subprocess dying
        mock_process.is_alive.side_effect = [True, True, False]
        mock_queue.get.side_effect = Exception("Empty")
        
        mock_multiprocessing.Queue.return_value = mock_queue
        mock_multiprocessing.Process.return_value = mock_process
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = True
        
        with patch('builtins.print'):
            recorder.start()
            time.sleep(6)  # Wait for health check
    
    @patch('platform.system', return_value='Linux')
    @patch('pynput.mouse')
    def test_context_manager(self, mock_mouse, mock_platform):
        """Test using mouse recorder as context manager."""
        mock_listener = MagicMock()
        mock_mouse.Listener.return_value = mock_listener
        
        with MouseRecorder(event_callback=self.callback_mock) as recorder:
            recorder._is_macos = False
            time.sleep(0.1)
            self.assertTrue(recorder.is_recording())
        
        # Should stop after context exit
        self.assertFalse(recorder.is_recording())
    
    @patch('platform.system')
    def test_multiple_button_types(self, mock_platform):
        """Test handling different mouse buttons."""
        mock_platform.return_value = 'Linux'
        
        recorder = MouseRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        # Test left button
        recorder._on_click(10, 20, MockButton('left'), True)
        
        # Test right button
        recorder._on_click(30, 40, MockButton('right'), True)
        
        # Test middle button
        recorder._on_click(50, 60, MockButton('middle'), True)
        
        # Should have handled all buttons
        self.assertEqual(self.callback_mock.call_count, 3)


if __name__ == '__main__':
    unittest.main()

