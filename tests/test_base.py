"""Tests for the base recorder functionality."""

import unittest
import time
import threading
from unittest.mock import Mock, patch
from computeruse_datacollection.recorders.base import BaseRecorder


class TestRecorder(BaseRecorder):
    """Test implementation of BaseRecorder for testing purposes."""
    
    def __init__(self, event_callback=None):
        super().__init__(event_callback)
        self.start_called = False
        self.stop_called = False
        self.recording_duration = 0
    
    def _start_recording(self):
        """Simulate recording by sleeping."""
        self.start_called = True
        while self._recording and not self._stop_event.is_set():
            time.sleep(0.01)
            self.recording_duration += 0.01
    
    def _stop_recording(self):
        """Simulate stopping recording."""
        self.stop_called = True


class TestBaseRecorder(unittest.TestCase):
    """Test cases for BaseRecorder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.callback_mock = Mock()
        self.recorder = TestRecorder(event_callback=self.callback_mock)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.recorder.is_recording():
            self.recorder.stop()
    
    def test_initialization(self):
        """Test recorder initialization."""
        self.assertFalse(self.recorder.is_recording())
        self.assertEqual(self.recorder.event_callback, self.callback_mock)
        self.assertIsNone(self.recorder._thread)
        self.assertFalse(self.recorder._stop_event.is_set())
    
    def test_start_recording(self):
        """Test starting recording."""
        self.recorder.start()
        time.sleep(0.1)  # Give thread time to start
        
        self.assertTrue(self.recorder.is_recording())
        self.assertTrue(self.recorder.start_called)
        self.assertIsNotNone(self.recorder._thread)
        self.assertTrue(self.recorder._thread.is_alive())
    
    def test_stop_recording(self):
        """Test stopping recording."""
        self.recorder.start()
        time.sleep(0.1)
        self.recorder.stop()
        
        self.assertFalse(self.recorder.is_recording())
        self.assertTrue(self.recorder.stop_called)
        self.assertTrue(self.recorder._stop_event.is_set())
    
    def test_double_start(self):
        """Test that starting twice doesn't create multiple threads."""
        self.recorder.start()
        first_thread = self.recorder._thread
        time.sleep(0.05)
        
        self.recorder.start()  # Try to start again
        second_thread = self.recorder._thread
        
        self.assertEqual(first_thread, second_thread)
        self.recorder.stop()
    
    def test_stop_when_not_recording(self):
        """Test that stopping when not recording is safe."""
        self.assertFalse(self.recorder.is_recording())
        self.recorder.stop()  # Should not raise an exception
        self.assertFalse(self.recorder.is_recording())
    
    def test_emit_event(self):
        """Test event emission."""
        event_type = "test_event"
        event_data = {"key": "value", "number": 42}
        
        self.recorder._emit_event(event_type, event_data)
        
        self.callback_mock.assert_called_once_with(event_type, event_data)
    
    def test_emit_event_no_callback(self):
        """Test event emission with no callback."""
        recorder = TestRecorder(event_callback=None)
        # Should not raise an exception
        recorder._emit_event("test", {"data": 1})
    
    def test_emit_event_callback_error(self):
        """Test that callback errors are handled gracefully."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        recorder = TestRecorder(event_callback=error_callback)
        
        # Should not raise an exception
        with patch('builtins.print') as mock_print:
            recorder._emit_event("test", {"data": 1})
            # Verify error was printed
            self.assertTrue(any("Error in event callback" in str(call) 
                              for call in mock_print.call_args_list))
    
    def test_context_manager(self):
        """Test using recorder as context manager."""
        with TestRecorder(event_callback=self.callback_mock) as recorder:
            self.assertTrue(recorder.is_recording())
            time.sleep(0.1)
        
        # After exiting context, recording should stop
        self.assertFalse(recorder.is_recording())
        self.assertTrue(recorder.stop_called)
    
    def test_recording_loop_error_handling(self):
        """Test that errors in recording loop are handled."""
        class ErrorRecorder(BaseRecorder):
            def _start_recording(self):
                raise RuntimeError("Test error")
            
            def _stop_recording(self):
                pass
        
        recorder = ErrorRecorder()
        with patch('builtins.print') as mock_print:
            recorder.start()
            time.sleep(0.1)
            
            # Check that error was printed
            self.assertTrue(any("Error in recording loop" in str(call) 
                              for call in mock_print.call_args_list))
            
            self.assertFalse(recorder.is_recording())
    
    def test_thread_cleanup(self):
        """Test that thread is properly cleaned up after stopping."""
        self.recorder.start()
        time.sleep(0.1)
        thread = self.recorder._thread
        
        self.recorder.stop()
        time.sleep(0.1)
        
        # Thread should be joined and no longer alive
        self.assertFalse(thread.is_alive())
        self.assertIsNone(self.recorder._thread)
    
    def test_stop_event_set_on_stop(self):
        """Test that stop event is set when stopping."""
        self.recorder.start()
        time.sleep(0.1)
        
        self.assertFalse(self.recorder._stop_event.is_set())
        self.recorder.stop()
        self.assertTrue(self.recorder._stop_event.is_set())
    
    def test_concurrent_access(self):
        """Test thread safety of start/stop operations."""
        def start_stop_cycle():
            for _ in range(5):
                self.recorder.start()
                time.sleep(0.01)
                self.recorder.stop()
                time.sleep(0.01)
        
        # Run multiple threads doing start/stop
        threads = [threading.Thread(target=start_stop_cycle) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should end in stopped state
        self.assertFalse(self.recorder.is_recording())


if __name__ == '__main__':
    unittest.main()

