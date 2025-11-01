"""Tests for the keyboard recorder."""

import unittest
import time
import platform
from unittest.mock import Mock, patch, MagicMock
from computeruse_datacollection.recorders.keyboard import KeyboardRecorder


class MockKey:
    """Mock pynput key object."""
    def __init__(self, char=None, name=None):
        self.char = char
        self.name = name


class TestKeyboardRecorder(unittest.TestCase):
    """Test cases for KeyboardRecorder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.callback_mock = Mock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Ensure recorder is stopped
        if hasattr(self, 'recorder') and self.recorder.is_recording():
            self.recorder.stop()
    
    def test_initialization(self):
        """Test keyboard recorder initialization."""
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        
        self.assertFalse(recorder.is_recording())
        self.assertEqual(recorder.event_callback, self.callback_mock)
        self.assertIsNone(recorder._listener)
        self.assertIsNone(recorder._process)
        self.assertIsNone(recorder._event_queue)
        self.assertEqual(recorder._is_macos, platform.system() == 'Darwin')
    
    def test_get_key_name_char(self):
        """Test getting key name for character keys."""
        recorder = KeyboardRecorder()
        key = MockKey(char='a')
        
        key_name = recorder._get_key_name(key)
        self.assertEqual(key_name, 'a')
    
    def test_get_key_name_special(self):
        """Test getting key name for special keys."""
        recorder = KeyboardRecorder()
        key = MockKey(name='shift')
        
        key_name = recorder._get_key_name(key)
        self.assertEqual(key_name, 'shift')
    
    def test_get_key_name_fallback(self):
        """Test getting key name for unknown keys."""
        recorder = KeyboardRecorder()
        key = "unknown_key"
        
        key_name = recorder._get_key_name(key)
        self.assertEqual(key_name, str(key))
    
    @patch('platform.system')
    @patch('pynput.keyboard')
    def test_start_recording_non_macos(self, mock_keyboard, mock_platform):
        """Test starting keyboard recording on non-macOS platforms."""
        mock_platform.return_value = 'Linux'
        mock_listener = MagicMock()
        mock_keyboard.Listener.return_value = mock_listener
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder.start()
        time.sleep(0.2)
        
        # Verify listener was created and started
        mock_keyboard.Listener.assert_called_once()
        mock_listener.start.assert_called_once()
        self.assertTrue(recorder.is_recording())
        
        recorder.stop()
        time.sleep(0.1)
        mock_listener.stop.assert_called_once()
    
    @patch('platform.system')
    def test_on_press_event(self, mock_platform):
        """Test handling key press events."""
        mock_platform.return_value = 'Linux'
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        key = MockKey(char='x')
        recorder._on_press(key)
        
        # Verify event was emitted
        self.callback_mock.assert_called_once()
        call_args = self.callback_mock.call_args
        self.assertEqual(call_args[0][0], "keyboard")
        self.assertEqual(call_args[0][1]["key"], "x")
        self.assertEqual(call_args[0][1]["action"], "press")
    
    @patch('platform.system')
    def test_on_release_event(self, mock_platform):
        """Test handling key release events."""
        mock_platform.return_value = 'Linux'
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        key = MockKey(name='enter')
        recorder._on_release(key)
        
        # Verify event was emitted
        self.callback_mock.assert_called_once()
        call_args = self.callback_mock.call_args
        self.assertEqual(call_args[0][0], "keyboard")
        self.assertEqual(call_args[0][1]["key"], "enter")
        self.assertEqual(call_args[0][1]["action"], "release")
    
    @patch('platform.system')
    def test_event_not_emitted_when_not_recording(self, mock_platform):
        """Test that events are not emitted when not recording."""
        mock_platform.return_value = 'Linux'
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = False
        
        key = MockKey(char='a')
        recorder._on_press(key)
        recorder._on_release(key)
        
        # No events should be emitted
        self.callback_mock.assert_not_called()
    
    @patch('platform.system')
    def test_event_handler_error_handling(self, mock_platform):
        """Test that errors in event handlers are caught."""
        mock_platform.return_value = 'Linux'
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        # Make callback raise an error
        self.callback_mock.side_effect = Exception("Test error")
        
        # Should not raise exception
        with patch('builtins.print'):
            key = MockKey(char='b')
            recorder._on_press(key)  # Should handle error gracefully
    
    @patch('platform.system')
    @patch('multiprocessing.Queue')
    @patch('multiprocessing.Process')
    def test_start_recording_macos(self, mock_process_class, mock_queue_class, mock_platform):
        """Test starting keyboard recording on macOS."""
        mock_platform.return_value = 'Darwin'
        mock_queue = MagicMock()
        mock_process = MagicMock()
        mock_process.is_alive.return_value = True
        
        mock_queue_class.return_value = mock_queue
        mock_process_class.return_value = mock_process
        
        # Mock queue to return empty (timeout) then stop
        mock_queue.get.side_effect = Exception("Empty")
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
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
    @patch('computeruse_datacollection.recorders.keyboard.multiprocessing')
    def test_macos_event_queue_processing(self, mock_multiprocessing, mock_platform):
        """Test that macOS subprocess events are processed correctly."""
        mock_platform.return_value = 'Darwin'
        mock_queue = MagicMock()
        mock_process = MagicMock()
        mock_process.is_alive.return_value = True
        
        # Simulate queue returning an event then timing out
        mock_queue.get.side_effect = [
            {"key": "a", "action": "press"},
            Exception("Empty")
        ]
        
        mock_multiprocessing.Queue.return_value = mock_queue
        mock_multiprocessing.Process.return_value = mock_process
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = True
        recorder.start()
        time.sleep(0.3)
        
        # Check that event was processed
        calls = self.callback_mock.call_args_list
        if calls:
            self.assertEqual(calls[0][0][0], "keyboard")
            self.assertEqual(calls[0][0][1]["key"], "a")
            self.assertEqual(calls[0][0][1]["action"], "press")
        
        recorder.stop()
    
    @patch('platform.system')
    @patch('computeruse_datacollection.recorders.keyboard.multiprocessing')
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
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = True
        
        with patch('builtins.print'):
            recorder.start()
            time.sleep(6)  # Wait for health check (happens every 5 seconds)
            
            # Recording should have stopped due to dead subprocess
            # (after the health check triggers)
    
    @patch('platform.system', return_value='Linux')
    @patch('pynput.keyboard')
    def test_context_manager(self, mock_keyboard, mock_platform):
        """Test using keyboard recorder as context manager."""
        mock_listener = MagicMock()
        mock_keyboard.Listener.return_value = mock_listener
        
        with KeyboardRecorder(event_callback=self.callback_mock) as recorder:
            recorder._is_macos = False
            time.sleep(0.1)
            self.assertTrue(recorder.is_recording())
        
        # Should stop after context exit
        self.assertFalse(recorder.is_recording())
    
    @patch('platform.system')
    def test_multiple_key_types(self, mock_platform):
        """Test handling different types of keys."""
        mock_platform.return_value = 'Linux'
        
        recorder = KeyboardRecorder(event_callback=self.callback_mock)
        recorder._is_macos = False
        recorder._recording = True
        
        # Test character key
        recorder._on_press(MockKey(char='z'))
        
        # Test special key
        recorder._on_press(MockKey(name='ctrl'))
        
        # Test key with no char or name
        class WeirdKey:
            pass
        recorder._on_press(WeirdKey())
        
        # Should have handled all keys
        self.assertEqual(self.callback_mock.call_count, 3)


if __name__ == '__main__':
    unittest.main()

