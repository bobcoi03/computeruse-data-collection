"""Session export functionality."""

from pathlib import Path
from typing import Optional
from computeruse_datacollection.utils.compression import zip_session
from computeruse_datacollection.core.config import Config


class SessionExporter:
    """Handles exporting sessions to shareable formats."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the exporter.
        
        Args:
            config: Configuration object, or None to load from file
        """
        self.config = config or Config.load()
    
    def export_session(self, session_id: str, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export a session to a zip file.
        
        Args:
            session_id: Session identifier to export
            output_path: Optional custom output path, defaults to session_<id>.zip
            
        Returns:
            Path to exported zip file, or None if failed
        """
        # Get session directory
        session_dir = self.config.get_storage_path() / f"session_{session_id}"
        
        if not session_dir.exists():
            print(f"Session not found: {session_id}")
            return None
        
        # Determine output path
        if output_path is None:
            output_path = Path.cwd() / f"session_{session_id}.zip"
        else:
            output_path = Path(output_path)
        
        # Create zip file
        success = zip_session(session_dir, output_path, include_readme=True)
        
        if success:
            print(f"Session exported to: {output_path}")
            return output_path
        else:
            print(f"Failed to export session: {session_id}")
            return None
    
    def export_multiple_sessions(self, session_ids: list, output_path: Optional[Path] = None) -> Optional[Path]:
        """Export multiple sessions to a single zip file.
        
        Args:
            session_ids: List of session identifiers to export
            output_path: Optional custom output path
            
        Returns:
            Path to exported zip file, or None if failed
        """
        import zipfile
        from computeruse_datacollection.utils.compression import _generate_export_readme
        
        if not session_ids:
            print("No sessions to export")
            return None
        
        # Determine output path
        if output_path is None:
            output_path = Path.cwd() / "exported_sessions.zip"
        else:
            output_path = Path(output_path)
        
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add each session
                for session_id in session_ids:
                    session_dir = self.config.get_storage_path() / f"session_{session_id}"
                    
                    if not session_dir.exists():
                        print(f"Warning: Session not found: {session_id}")
                        continue
                    
                    # Add all files from session
                    for file_path in session_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(self.config.get_storage_path())
                            zipf.write(file_path, arcname=arcname)
                
                # Add README
                readme_content = _generate_export_readme()
                zipf.writestr('DATA_FORMAT_README.txt', readme_content)
            
            print(f"Exported {len(session_ids)} sessions to: {output_path}")
            return output_path
        
        except Exception as e:
            print(f"Error exporting sessions: {e}")
            return None

