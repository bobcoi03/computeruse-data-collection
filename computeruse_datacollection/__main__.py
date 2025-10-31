"""Main entry point for computeruse-datacollection package."""

import sys
from computeruse_datacollection.cli import main


def main_entry():
    """Main entry point that can be called by setuptools."""
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main_entry()

