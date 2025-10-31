"""Command-line interface for computeruse-datacollection."""

import argparse
import sys
import time
from pathlib import Path
from computeruse_datacollection.core.collector import DataCollector
from computeruse_datacollection.core.config import Config
from computeruse_datacollection.core.exporter import SessionExporter
from computeruse_datacollection.utils.compression import get_human_readable_size


def cmd_start(args):
    """Start a recording session from CLI."""
    config = Config.load()
    
    # Override config based on arguments
    if args.no_keyboard:
        config.keyboard_enabled = False
    if args.no_mouse:
        config.mouse_enabled = False
    if args.no_screen:
        config.screen_enabled = False
    if args.no_audio:
        config.audio_enabled = False
    
    collector = DataCollector(config)
    
    print("Starting recording...")
    success = collector.start_recording(args.name)
    
    if not success:
        print("Failed to start recording. Please check permissions.")
        return 1
    
    print("Recording started. Press Ctrl+C to stop.")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping recording...")
        collector.stop_recording()
        print("Recording stopped.")
        return 0


def cmd_list(args):
    """List all recorded sessions."""
    config = Config.load()
    collector = DataCollector(config)
    
    sessions = collector.list_sessions()
    
    if not sessions:
        print("No recorded sessions found.")
        return 0
    
    print(f"\nFound {len(sessions)} session(s):\n")
    
    for session_id in sessions:
        metadata = collector.get_session_metadata(session_id)
        if metadata:
            print(f"Session ID: {session_id}")
            print(f"  Start: {metadata.get('start_time', 'Unknown')}")
            print(f"  Duration: {metadata.get('duration_seconds', 0):.1f}s")
            
            recorders = metadata.get('recorders_enabled', {})
            enabled = [k for k, v in recorders.items() if v]
            print(f"  Recorded: {', '.join(enabled)}")
            print()
    
    return 0


def cmd_export(args):
    """Export a session to a zip file."""
    config = Config.load()
    exporter = SessionExporter(config)
    
    output_path = Path(args.output) if args.output else None
    
    result = exporter.export_session(args.session_id, output_path)
    
    if result:
        print(f"Session exported successfully to: {result}")
        return 0
    else:
        print("Failed to export session.")
        return 1


def cmd_delete(args):
    """Delete a recorded session."""
    config = Config.load()
    collector = DataCollector(config)
    
    # Confirm deletion
    if not args.yes:
        response = input(f"Delete session {args.session_id}? This cannot be undone. (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    
    success = collector.delete_session(args.session_id)
    
    if success:
        print(f"Session {args.session_id} deleted successfully.")
        return 0
    else:
        print("Failed to delete session.")
        return 1


def cmd_config(args):
    """View or modify configuration."""
    config = Config.load()
    
    if args.show:
        # Show current config
        print("\nCurrent Configuration:\n")
        print(f"Keyboard enabled: {config.keyboard_enabled}")
        print(f"Mouse enabled: {config.mouse_enabled}")
        print(f"Screen enabled: {config.screen_enabled}")
        print(f"Audio enabled: {config.audio_enabled}")
        print(f"\nScreen quality: {config.screen_quality}")
        print(f"Screen FPS: {config.screen_fps}")
        print(f"\nStorage path: {config.storage_path}")
        print(f"Max storage: {config.max_storage_gb} GB")
        print(f"Compression: {config.compression_enabled}")
        return 0
    
    # Update config if flags provided
    updated = False
    
    if args.screen_quality:
        config.screen_quality = args.screen_quality
        updated = True
    
    if args.screen_fps:
        config.screen_fps = args.screen_fps
        updated = True
    
    if args.storage_path:
        config.storage_path = args.storage_path
        updated = True
    
    if args.max_storage:
        config.max_storage_gb = args.max_storage
        updated = True
    
    if updated:
        config.save()
        print("Configuration updated.")
        return 0
    
    # No flags, show config
    return cmd_config(type('Args', (), {'show': True})())


def cmd_info(args):
    """Show information about storage usage."""
    config = Config.load()
    collector = DataCollector(config)
    
    sessions = collector.list_sessions()
    total_size = collector.get_total_storage_size()
    
    print(f"\nStorage Information:\n")
    print(f"Location: {config.get_storage_path()}")
    print(f"Total sessions: {len(sessions)}")
    print(f"Total size: {get_human_readable_size(total_size)}")
    print(f"Max allowed: {config.max_storage_gb} GB")
    
    # Calculate percentage
    max_bytes = config.get_max_storage_bytes()
    percentage = (total_size / max_bytes * 100) if max_bytes > 0 else 0
    print(f"Usage: {percentage:.1f}%")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Computer Use Data Collection - Privacy-first data collection for AI training"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start recording a session")
    start_parser.add_argument("--name", help="Optional session name")
    start_parser.add_argument("--no-keyboard", action="store_true", help="Disable keyboard recording")
    start_parser.add_argument("--no-mouse", action="store_true", help="Disable mouse recording")
    start_parser.add_argument("--no-screen", action="store_true", help="Disable screen recording")
    start_parser.add_argument("--no-audio", action="store_true", help="Disable audio recording")
    start_parser.set_defaults(func=cmd_start)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all recorded sessions")
    list_parser.set_defaults(func=cmd_list)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export a session to zip file")
    export_parser.add_argument("session_id", help="Session ID to export")
    export_parser.add_argument("--output", "-o", help="Output path for zip file")
    export_parser.set_defaults(func=cmd_export)
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a recorded session")
    delete_parser.add_argument("session_id", help="Session ID to delete")
    delete_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=cmd_delete)
    
    # Config command
    config_parser = subparsers.add_parser("config", help="View or modify configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    config_parser.add_argument("--screen-quality", choices=["high", "low"], help="Set screen quality")
    config_parser.add_argument("--screen-fps", type=int, help="Set screen FPS")
    config_parser.add_argument("--storage-path", help="Set storage path")
    config_parser.add_argument("--max-storage", type=int, help="Set max storage in GB")
    config_parser.set_defaults(func=cmd_config)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show storage information")
    info_parser.set_defaults(func=cmd_info)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        # No command provided, launch GUI
        try:
            print("Launching GUI...")
            from computeruse_datacollection.gui.main_window import main as gui_main
            print("GUI module imported successfully")
            gui_main()
            return 0
        except Exception as e:
            print(f"Error launching GUI: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # Execute command
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

