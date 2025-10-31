"""Compression utilities for exporting session data."""

import zipfile
from pathlib import Path
from typing import Optional


def zip_session(session_dir: Path, output_path: Path, include_readme: bool = True) -> bool:
    """Compress a session directory into a zip file.
    
    Args:
        session_dir: Path to the session directory
        output_path: Path where the zip file should be created
        include_readme: Whether to include a README explaining the data format
        
    Returns:
        True if successful, False otherwise
    """
    try:
        session_dir = Path(session_dir)
        output_path = Path(output_path)
        
        if not session_dir.exists():
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files in session directory
            for file_path in session_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(session_dir.parent)
                    zipf.write(file_path, arcname=arcname)
            
            # Add README if requested
            if include_readme:
                readme_content = _generate_export_readme()
                zipf.writestr('DATA_FORMAT_README.txt', readme_content)
        
        return True
    
    except Exception as e:
        print(f"Error creating zip file: {e}")
        return False


def _generate_export_readme() -> str:
    """Generate a README explaining the data format.
    
    Returns:
        README content as string
    """
    return """# Computer Use Data Collection - Exported Session

This archive contains a recorded session of computer use data.

## File Structure

- `metadata.json` - Session metadata (start time, duration, enabled recorders, settings)
- `events.jsonl` - Event stream in JSON Lines format (one JSON object per line)
- `screen_recording.mp4` - Screen capture video (if screen recording was enabled)

## Data Format

### metadata.json
Contains session-level information:
```json
{
  "session_id": "unique-uuid",
  "start_time": "2025-10-31T10:30:00Z",
  "end_time": "2025-10-31T10:45:00Z",
  "duration_seconds": 900,
  "recorders_enabled": {
    "keyboard": true,
    "mouse": true,
    "screen": true,
    "audio": false
  },
  "settings": {
    "screen_quality": "high",
    "screen_fps": 30,
    "screen_resolution": [1920, 1080]
  }
}
```

### events.jsonl
Each line is a JSON object representing an event:

**Keyboard Event:**
```json
{"type": "keyboard", "timestamp": "2025-10-31T10:30:01.123Z", "key": "a", "action": "press"}
{"type": "keyboard", "timestamp": "2025-10-31T10:30:01.234Z", "key": "a", "action": "release"}
```

**Mouse Event:**
```json
{"type": "mouse", "timestamp": "2025-10-31T10:30:02.456Z", "x": 100, "y": 250, "action": "move"}
{"type": "mouse", "timestamp": "2025-10-31T10:30:02.567Z", "x": 100, "y": 250, "button": "left", "action": "click"}
{"type": "mouse", "timestamp": "2025-10-31T10:30:03.678Z", "x": 100, "y": 250, "dx": 0, "dy": 1, "action": "scroll"}
```

## Using This Data

This data is formatted for training computer use AI agents. You can:

1. Parse `events.jsonl` line by line for streaming processing
2. Sync events with screen recording using timestamps
3. Train models to predict actions based on screen state
4. Analyze user behavior patterns

## Privacy

This data was collected with the user's explicit consent using open-source software.
All data was stored locally until the user chose to export and share it.

## Questions?

Visit: https://github.com/bobcoi03/computeruse-data-collection
"""


def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

