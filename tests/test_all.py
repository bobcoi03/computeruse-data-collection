"""Run all tests for the computeruse-data-collection package."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules
from tests import test_base, test_keyboard, test_mouse, test_screen


def create_test_suite():
    """Create a test suite containing all tests."""
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_suite.addTests(unittest.TestLoader().loadTestsFromModule(test_base))
    test_suite.addTests(unittest.TestLoader().loadTestsFromModule(test_keyboard))
    test_suite.addTests(unittest.TestLoader().loadTestsFromModule(test_mouse))
    test_suite.addTests(unittest.TestLoader().loadTestsFromModule(test_screen))
    
    return test_suite


def run_tests():
    """Run all tests and return the result."""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if successful, 1 if there were failures
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

