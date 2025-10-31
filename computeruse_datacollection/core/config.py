"""Configuration management for the data collection application."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Configuration settings for data collection."""
    
    # Recording options (defaults)
    keyboard_enabled: bool = True  # Runs in separate process on macOS to avoid tkinter conflicts
    mouse_enabled: bool = True  # Runs in separate process on macOS to avoid tkinter conflicts
    screen_enabled: bool = True  # Screen recording works with screencapture command
    audio_enabled: bool = False  # Audio recording disabled by default (optional feature)
    
    # Screen recording settings
    screen_quality: str = "high"  # "high" or "low"
    screen_fps: int = 30
    screen_resolution: Optional[tuple] = None  # None for native resolution
    
    # Privacy settings
    anonymize_text: bool = False
    blur_sensitive_areas: bool = False
    
    # Storage settings
    storage_path: str = "~/computer_use_data"
    max_storage_gb: int = 10
    compression_enabled: bool = True
    
    @classmethod
    def get_config_path(cls) -> Path:
        """Get the path to the configuration file.
        
        Returns:
            Path to config.json
        """
        config_dir = Path.home() / ".computeruse-collect"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"
    
    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file, or create default if not exists.
        
        Returns:
            Config instance
        """
        config_path = cls.get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return cls()
        else:
            # Create default config
            config = cls()
            config.save()
            return config
    
    def save(self):
        """Save configuration to file."""
        config_path = self.get_config_path()
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                data = asdict(self)
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.
        
        Returns:
            Dictionary representation of config
        """
        return asdict(self)
    
    def update(self, **kwargs):
        """Update config values.
        
        Args:
            **kwargs: Key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    def get_storage_path(self) -> Path:
        """Get the expanded storage path.
        
        Returns:
            Expanded Path object
        """
        return Path(self.storage_path).expanduser()
    
    def get_max_storage_bytes(self) -> int:
        """Get maximum storage in bytes.
        
        Returns:
            Max storage in bytes
        """
        return self.max_storage_gb * 1024 * 1024 * 1024

