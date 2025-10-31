"""Settings window for configuration options."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from computeruse_datacollection.core.config import Config


class SettingsWindow:
    """Settings configuration window."""
    
    def __init__(self, parent, config: Config):
        """Initialize the settings window.
        
        Args:
            parent: Parent window
            config: Configuration object
        """
        self.config = config
        
        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("550x600")
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the settings UI."""
        # Create canvas with scrollbar
        canvas = tk.Canvas(self.window, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout for canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Main container (now inside scrollable frame)
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Settings",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Screen Recording Settings
        screen_frame = ttk.LabelFrame(main_frame, text="Screen Recording", padding="10")
        screen_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        ttk.Label(screen_frame, text="Quality:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value=self.config.screen_quality)
        quality_combo = ttk.Combobox(
            screen_frame,
            textvariable=self.quality_var,
            values=["high", "low"],
            state="readonly",
            width=15
        )
        quality_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        ttk.Label(screen_frame, text="FPS:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.IntVar(value=self.config.screen_fps)
        fps_spinbox = ttk.Spinbox(
            screen_frame,
            from_=1,
            to=60,
            textvariable=self.fps_var,
            width=15
        )
        fps_spinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Privacy Settings
        privacy_frame = ttk.LabelFrame(main_frame, text="Privacy", padding="10")
        privacy_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        self.anonymize_var = tk.BooleanVar(value=self.config.anonymize_text)
        ttk.Checkbutton(
            privacy_frame,
            text="Anonymize text inputs",
            variable=self.anonymize_var
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.blur_var = tk.BooleanVar(value=self.config.blur_sensitive_areas)
        ttk.Checkbutton(
            privacy_frame,
            text="Blur sensitive areas",
            variable=self.blur_var
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Storage Settings
        storage_frame = ttk.LabelFrame(main_frame, text="Storage", padding="10")
        storage_frame.grid(row=3, column=0, columnspan=2, pady=(0, 15), sticky=(tk.W, tk.E))
        
        ttk.Label(storage_frame, text="Storage Path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(storage_frame)
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.storage_path_var = tk.StringVar(value=self.config.storage_path)
        path_entry = ttk.Entry(
            path_frame,
            textvariable=self.storage_path_var,
            width=30
        )
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(
            path_frame,
            text="Browse...",
            command=self._browse_storage_path,
            width=10
        ).grid(row=0, column=1, padx=(5, 0))
        
        ttk.Label(storage_frame, text="Max Storage (GB):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_storage_var = tk.IntVar(value=self.config.max_storage_gb)
        storage_spinbox = ttk.Spinbox(
            storage_frame,
            from_=1,
            to=1000,
            textvariable=self.max_storage_var,
            width=15
        )
        storage_spinbox.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.compression_var = tk.BooleanVar(value=self.config.compression_enabled)
        ttk.Checkbutton(
            storage_frame,
            text="Enable compression",
            variable=self.compression_var
        ).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings,
            width=15
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            width=15
        ).grid(row=0, column=1, padx=5)
    
    def _browse_storage_path(self):
        """Open directory browser for storage path."""
        directory = filedialog.askdirectory(
            title="Select Storage Directory",
            initialdir=self.storage_path_var.get()
        )
        if directory:
            self.storage_path_var.set(directory)
    
    def _save_settings(self):
        """Save settings and close window."""
        try:
            # Update config
            self.config.update(
                screen_quality=self.quality_var.get(),
                screen_fps=self.fps_var.get(),
                anonymize_text=self.anonymize_var.get(),
                blur_sensitive_areas=self.blur_var.get(),
                storage_path=self.storage_path_var.get(),
                max_storage_gb=self.max_storage_var.get(),
                compression_enabled=self.compression_var.get()
            )
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

