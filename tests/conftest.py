"""Pytest configuration and fixtures."""

import sys
from unittest.mock import MagicMock

# Mock problematic modules before any tests import them
# This prevents segfaults on macOS with cv2/numpy
sys.modules['cv2'] = MagicMock()

# Create a proper numpy mock with array functionality
numpy_mock = MagicMock()
numpy_mock.zeros = MagicMock(return_value=MagicMock())
numpy_mock.array = MagicMock(return_value=MagicMock())
sys.modules['numpy'] = numpy_mock

# Mock mss to avoid import errors
sys.modules['mss'] = MagicMock()
sys.modules['mss.mss'] = MagicMock()

# Mock pynput modules to avoid platform-specific import issues
pynput_keyboard_mock = MagicMock()
pynput_keyboard_mock.Listener = MagicMock()
sys.modules['pynput'] = MagicMock()
sys.modules['pynput.keyboard'] = pynput_keyboard_mock
sys.modules['pynput.mouse'] = MagicMock()

