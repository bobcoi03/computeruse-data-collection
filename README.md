# Computer Use Data Collection

A privacy-first application for collecting standardized computer use data to train AI agents.

## Overview

A simple, user-friendly program that records your computer interactions—keyboard inputs, mouse movements, screen recordings, and audio—to help train and improve AI agents. Unlike proprietary solutions, all data stays on your machine until you explicitly decide to share it.

**No coding required.** Just install and run.

## Why This Project?

As AI agents become more capable of computer use tasks, they need high-quality training data. However, current data collection methods are:
- **Fragmented**: Everyone uses different formats and collection methods
- **Privacy-invasive**: Data often gets uploaded automatically to remote servers
- **Closed-source**: No transparency in what's being collected or how

This library solves these problems by providing:
- **Standardized data format**: Consistent, well-documented schemas for interoperability
- **Local-first privacy**: All data stored locally; you control what gets shared and when
- **Full transparency**: Open-source code you can audit and modify

## Key Features

- **Easy to Use**: Simple GUI or command-line interface—no coding needed
- **Privacy by Design**: Everything stored locally on your machine
- **Standardized Format**: Common data schema for cross-platform compatibility
- **Selective Recording**: Choose what to record (keyboard, mouse, screen, audio)
- **Transparent**: Fully open-source and auditable
- **Your Data, Your Choice**: Export and share on your own terms
- **Lightweight**: Minimal performance impact on your system
- **User-Friendly Interface**: Clean, intuitive design for everyone

## System Requirements

- **Operating System**: macOS, Linux (Windows support coming soon)
- **Python**: 3.8 or higher (comes pre-installed on most systems)
- **Disk Space**: 100 MB for the app + storage for your recordings
- **RAM**: 200 MB minimum
- **For MP4 video**: ffmpeg (install with `brew install ffmpeg`)

Don't worry if you're not sure—the installer will check for you!

### macOS Sequoia Users

If you're on **macOS Sequoia (15.x)**:
- **All recording modules work!** (keyboard, mouse, screen)
- Uses separate processes to avoid tkinter/pynput conflicts
- Just grant Input Monitoring + Screen Recording permissions in System Preferences

## Installation

> **Note**: Most Mac and Linux systems come with Python pre-installed. If you get an error, you may need to install Python first from [python.org](https://python.org).

### Install from Source

```bash
git clone https://github.com/bobcoi03/computeruse-data-collection
cd computeruse-data-collection
pip install .
```

## Quick Start

### Launch the Application

**Option 1: Graphical Interface (Recommended)**
```bash
python3 -m computeruse_datacollection
```

This opens a simple window where you can:
- Click "Start Recording" to begin a session
- Choose what to record (keyboard, mouse, screen, audio)
- View your recorded sessions
- Export data when you're ready to share

**Option 2: Command Line**
```bash
# Start recording with default settings
computeruse-collect start

# Start with specific options
computeruse-collect start --no-screen --no-audio

# View your sessions
computeruse-collect list

# Export a session for sharing
computeruse-collect export session_id --output ./my_data.zip
```

### Your First Recording

1. Run `computeruse-collect` to open the app
2. Click "Start Recording" 
3. Do your computer work as normal
4. Click "Stop Recording" when done
5. Your data is saved locally in `~/computer_use_data/`

## Where Are Files Stored?

**Default Storage Location:**
```
~/computer_use_data/
```

On macOS/Linux, this expands to:
```
/Users/YourUsername/computer_use_data/
```

**Folder Structure:**
Each recording session creates its own folder:
```
~/computer_use_data/
├── session_<uuid1>/
│   ├── events.jsonl          # Keyboard & mouse events with timestamps
│   ├── screen_recording.mp4  # Screen video (H.264 MP4 format)
│   └── metadata.json          # Session information
├── session_<uuid2>/
│   ├── events.jsonl
│   ├── screen_recording.mp4
│   └── metadata.json
└── ...
```

**Accessing Your Files:**
- **Via GUI**: Open the app → Click "View Sessions" → Select a session → Click "Export"
- **Via Terminal**: 
  ```bash
  # Open the storage folder
  open ~/computer_use_data
  
  # List all sessions
  ls ~/computer_use_data
  ```

**Changing Storage Location:**
You can change where files are stored:
1. Open the app
2. Click "Settings"
3. Find "Storage Path" and click "Browse..."
4. Select your preferred location

## Simple Interface

The app provides a clean, easy-to-understand interface:

```
┌─────────────────────────────────────┐
│  Computer Use Data Collection       │
├─────────────────────────────────────┤
│                                     │
│  Status: Not Recording              │
│                                     │
│  ┌─── Recording Options ─────────┐ │
│  │ [x] Keyboard                  │ │
│  │ [x] Mouse                     │ │
│  │ [x] Screen                    │ │
│  │ [ ] Audio                     │ │
│  └───────────────────────────────┘ │
│                                     │
│     [ Start Recording ]             │
│                                     │
│  Recent Sessions: 3                 │
│  Total Data: 234 MB                 │
│                                     │
│  [ View Sessions ]  [ Settings ]    │
└─────────────────────────────────────┘
```

## Data Format

All collected data follows a standardized JSON schema with timestamps, making it easy to:
- Replay sessions for debugging
- Train AI models with consistent inputs
- Share data across different platforms and research groups

Example data structure:
```json
{
  "session_id": "uuid-here",
  "timestamp": "2025-10-31T10:30:00Z",
  "events": [
    {
      "type": "keyboard",
      "timestamp": 1234567890.123,
      "key": "a",
      "action": "press"
    },
    {
      "type": "mouse",
      "timestamp": 1234567890.456,
      "x": 100,
      "y": 250,
      "action": "move"
    }
  ]
}
```

## Privacy & Data Control

### What Gets Collected?
- Keyboard events (what keys are pressed)
- Mouse coordinates and clicks
- Screen recordings (optional, configurable quality)
- Audio input/output (optional, off by default)

### What Doesn't Get Collected?
- No automatic uploads to any server
- No personally identifiable information (unless you explicitly include it)
- No background collection when not in a recording session

### Sharing Your Data
When you're ready to share, you have full control:

**Via GUI:**
1. Open the app with `computeruse-collect`
2. Click "View Sessions" to review what you've recorded
3. Select sessions you want to share
4. Click "Export" to create a shareable file
5. Upload the exported file to wherever you choose (research project, AI company, etc.)

**Via Command Line:**
```bash
# Review your sessions
computeruse-collect list

# Export specific sessions
computeruse-collect export session_123 --output ./shared_data.zip

# You then upload shared_data.zip wherever you want
```

## Use Cases

- **Help Train AI**: Contribute your computer interactions to improve AI agents
- **Support Research**: Help researchers understand how people work with computers
- **Earn Rewards**: Some AI companies may compensate users for quality data contributions
- **Personal Productivity**: Analyze your own work patterns
- **Accessibility**: Help improve technology for users with different abilities
- **Open Science**: Contribute to open-source AI development

## Configuration

Customize collection settings through the app or config file:

**Via GUI Settings:**
- Open the app and click "Settings" 
- Adjust privacy, performance, and storage options
- Changes take effect immediately

**Via Command Line:**
```bash
# Open settings
computeruse-collect config

# Or set specific options
computeruse-collect config --anonymize-text --screen-fps 1 --max-storage 10
```

**Via Config File** (`~/.computeruse-collect/config.json`):
```json
{
  "privacy": {
    "anonymize_text": true,
    "blur_sensitive_areas": true
  },
  "performance": {
    "screen_fps": 1,
    "screen_resolution": [1280, 720]
  },
  "storage": {
    "max_storage_gb": 10,
    "compression": true,
    "data_path": "~/computer_use_data"
  }
}
```

## Troubleshooting

### The `computeruse-collect` command isn't found
Make sure Python's bin directory is in your PATH. Try:
```bash
python -m computeruse_datacollection
```

### "macOS 26 (2600) or later required" error
If you see this error on macOS Sequoia, uninstall the mss library:
```bash
pip uninstall mss
```
The app will automatically use native macOS APIs for screen capture instead.

### Permission errors on macOS
The app needs permission to record your screen/keyboard. Go to:
`System Preferences → Security & Privacy → Privacy`

### App won't start
Make sure you have Python 3.8+:
```bash
python --version
```

## Contributing

We'd love your help making this better! You don't need to be a developer:
- **Report bugs**: Found something broken? Let us know!
- **Suggest features**: Have ideas? Share them!
- **Improve docs**: Help make this README clearer
- **Code contributions**: Add features or fix bugs
- **Translations**: Help make this accessible worldwide

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Ethical Guidelines

This tool is designed for consensual data collection. Users should:
- Only record their own computer use
- Be aware when recording is active
- Review data before sharing
- Never record others without explicit consent
- Never use for surveillance or malicious purposes

## License

MIT License - see [LICENSE](LICENSE) file for details.
