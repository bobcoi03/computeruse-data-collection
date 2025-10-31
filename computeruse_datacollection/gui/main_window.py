"""Main GUI window for the data collection application."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from computeruse_datacollection.core.collector import DataCollector
from computeruse_datacollection.core.config import Config
from computeruse_datacollection.utils.compression import get_human_readable_size


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        self.root = tk.Tk()
        self.root.title("Computer Use Data Collection")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        
        # Load config
        self.config = Config.load()
        self.collector = DataCollector(self.config)
        
        # Recording state
        self.is_recording = False
        self.update_timer_id: Optional[str] = None
        
        # Build UI
        self._build_ui()
        
        # Start update loop
        self._update_status()
    
    def _build_ui(self):
        """Build the user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Computer Use Data Collection",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status indicator
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        self.status_indicator = ttk.Label(
            self.status_frame,
            text="●",
            font=("Arial", 20),
            foreground="gray"
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Not Recording",
            font=("Arial", 12)
        )
        self.status_label.grid(row=0, column=1)
        
        # Recording options frame
        options_frame = ttk.LabelFrame(main_frame, text="Recording Options", padding="15")
        options_frame.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Checkboxes for recording options
        self.keyboard_var = tk.BooleanVar(value=self.config.keyboard_enabled)
        self.mouse_var = tk.BooleanVar(value=self.config.mouse_enabled)
        self.screen_var = tk.BooleanVar(value=self.config.screen_enabled)
        
        ttk.Checkbutton(
            options_frame,
            text="☑ Keyboard",
            variable=self.keyboard_var,
            command=self._update_config
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(
            options_frame,
            text="☑ Mouse",
            variable=self.mouse_var,
            command=self._update_config
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(
            options_frame,
            text="☑ Screen",
            variable=self.screen_var,
            command=self._update_config
        ).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Start/Stop button
        self.record_button = ttk.Button(
            main_frame,
            text="Start Recording",
            command=self._toggle_recording,
            width=20
        )
        self.record_button.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        # Session info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        self.session_count_label = ttk.Label(info_frame, text="Recent Sessions: 0")
        self.session_count_label.grid(row=0, column=0, pady=5)
        
        self.storage_label = ttk.Label(info_frame, text="Total Data: 0 B")
        self.storage_label.grid(row=1, column=0, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2)
        
        ttk.Button(
            button_frame,
            text="View Sessions",
            command=self._open_sessions_window,
            width=15
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Settings",
            command=self._open_settings_window,
            width=15
        ).grid(row=0, column=1, padx=5)
    
    def _toggle_recording(self):
        """Toggle recording on/off."""
        if not self.is_recording:
            # Start recording
            try:
                print("Starting recording...")
                success = self.collector.start_recording()
                print(f"Recording start result: {success}")
                if success:
                    self.is_recording = True
                    self._update_recording_state()
                else:
                    messagebox.showerror(
                        "Error",
                        "Failed to start recording. Please check permissions."
                    )
            except Exception as e:
                print(f"Error starting recording: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror(
                    "Error",
                    f"Failed to start recording:\n{str(e)}"
                )
        else:
            # Stop recording
            try:
                self.collector.stop_recording()
                self.is_recording = False
                self._update_recording_state()
            except Exception as e:
                print(f"Error stopping recording: {e}")
                import traceback
                traceback.print_exc()
    
    def _update_recording_state(self):
        """Update UI to reflect recording state."""
        if self.is_recording:
            self.status_indicator.config(foreground="red")
            self.status_label.config(text="Recording")
            self.record_button.config(text="Stop Recording")
            
            # Disable checkboxes during recording
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Checkbutton):
                    widget.config(state='disabled')
        else:
            self.status_indicator.config(foreground="gray")
            self.status_label.config(text="Not Recording")
            self.record_button.config(text="Start Recording")
            
            # Enable checkboxes
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Checkbutton):
                    widget.config(state='normal')
    
    def _update_config(self):
        """Update configuration when checkboxes change."""
        self.config.update(
            keyboard_enabled=self.keyboard_var.get(),
            mouse_enabled=self.mouse_var.get(),
            screen_enabled=self.screen_var.get()
        )
    
    def _update_status(self):
        """Update session count and storage info."""
        # Update session count
        sessions = self.collector.list_sessions()
        self.session_count_label.config(text=f"Recent Sessions: {len(sessions)}")
        
        # Update storage size
        total_size = self.collector.get_total_storage_size()
        size_str = get_human_readable_size(total_size)
        self.storage_label.config(text=f"Total Data: {size_str}")
        
        # Schedule next update
        self.update_timer_id = self.root.after(2000, self._update_status)
    
    def _open_sessions_window(self):
        """Open the sessions viewer window."""
        from computeruse_datacollection.gui.sessions_window import SessionsWindow
        SessionsWindow(self.root, self.collector)
    
    def _open_settings_window(self):
        """Open the settings window."""
        from computeruse_datacollection.gui.settings_window import SettingsWindow
        SettingsWindow(self.root, self.config)
    
    def run(self):
        """Start the GUI main loop."""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
    
    def _on_closing(self):
        """Handle window close event."""
        if self.is_recording:
            if messagebox.askokcancel(
                "Recording in Progress",
                "Recording is still active. Stop recording and exit?"
            ):
                self.collector.stop_recording()
                self._cleanup()
                self.root.destroy()
        else:
            self._cleanup()
            self.root.destroy()
    
    def _cleanup(self):
        """Cleanup before closing."""
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)


def main():
    """Main entry point for GUI."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()

