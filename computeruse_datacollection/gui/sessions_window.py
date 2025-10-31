"""Sessions viewer window for managing recorded sessions."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from computeruse_datacollection.core.collector import DataCollector
from computeruse_datacollection.core.exporter import SessionExporter
from computeruse_datacollection.utils.compression import get_human_readable_size
from computeruse_datacollection.utils.storage import SessionStorage


class SessionsWindow:
    """Sessions management window."""
    
    def __init__(self, parent, collector: DataCollector):
        """Initialize the sessions window.
        
        Args:
            parent: Parent window
            collector: DataCollector instance
        """
        self.collector = collector
        self.exporter = SessionExporter(collector.config)
        self.sessions_data = []  # Store session data for sorting
        self.sort_column = "date"
        self.sort_reverse = True  # Latest first
        
        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title("Recorded Sessions")
        self.window.geometry("1000x700")  # Larger window
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self._build_ui()
        self._load_sessions()
    
    def _build_ui(self):
        """Build the sessions UI."""
        # Main container
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Recorded Sessions",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Sessions list with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create treeview with multi-select
        columns = ("session_id", "date", "duration", "size")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="extended",  # Allow multi-select
            height=20
        )
        
        # Define headings with sort indicators
        self.tree.heading("session_id", text="Session ID", 
                         command=lambda: self._sort_by("session_id"))
        self.tree.heading("date", text="Date ▼", 
                         command=lambda: self._sort_by("date"))
        self.tree.heading("duration", text="Duration", 
                         command=lambda: self._sort_by("duration"))
        self.tree.heading("size", text="Size", 
                         command=lambda: self._sort_by("size"))
        
        # Define column widths (wider for better visibility)
        self.tree.column("session_id", width=350)
        self.tree.column("date", width=180)
        self.tree.column("duration", width=120)
        self.tree.column("size", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Details frame
        details_frame = ttk.LabelFrame(main_frame, text="Session Details", padding="10")
        details_frame.grid(row=2, column=0, pady=(15, 0), sticky=(tk.W, tk.E))
        
        self.details_text = tk.Text(details_frame, height=6, width=60, wrap=tk.WORD)
        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.details_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(15, 0))
        
        self.export_button = ttk.Button(
            button_frame,
            text="Export Selected",
            command=self._export_selected,
            width=15,
            state=tk.DISABLED
        )
        self.export_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Export All",
            command=self._export_all,
            width=15
        ).grid(row=0, column=1, padx=5)
        
        self.delete_button = ttk.Button(
            button_frame,
            text="Delete",
            command=self._delete_session,
            width=15,
            state=tk.DISABLED
        )
        self.delete_button.grid(row=0, column=2, padx=5)
        
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self._load_sessions,
            width=15
        ).grid(row=0, column=3, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            width=15
        ).grid(row=0, column=4, padx=5)
    
    def _load_sessions(self):
        """Load and display all sessions."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get sessions
        session_ids = self.collector.list_sessions()
        self.sessions_data = []
        
        for session_id in session_ids:
            metadata = self.collector.get_session_metadata(session_id)
            if metadata:
                # Parse date
                start_time = metadata.get("start_time", "Unknown")
                date_obj = None
                if start_time != "Unknown":
                    try:
                        date_obj = datetime.fromisoformat(start_time)
                        date_str = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        date_str = start_time
                else:
                    date_str = "Unknown"
                
                # Format duration
                duration = metadata.get("duration_seconds", 0)
                if duration:
                    mins, secs = divmod(int(duration), 60)
                    duration_str = f"{mins}m {secs}s"
                else:
                    duration_str = "N/A"
                
                # Get size
                storage = SessionStorage(session_id, self.collector.config.get_storage_path())
                size = storage.get_size()
                size_str = get_human_readable_size(size)
                
                # Store session data for sorting
                self.sessions_data.append({
                    "session_id": session_id,
                    "date": date_str,
                    "date_obj": date_obj,
                    "duration": duration_str,
                    "duration_seconds": duration,
                    "size": size_str,
                    "size_bytes": size
                })
        
        # Sort by date (latest first) by default
        self._sort_and_display()
    
    def _sort_by(self, column):
        """Sort sessions by column.
        
        Args:
            column: Column name to sort by
        """
        # Toggle sort direction if same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = True if column == "date" else False
        
        self._sort_and_display()
    
    def _sort_and_display(self):
        """Sort sessions data and display in tree."""
        # Sort data
        if self.sort_column == "date":
            self.sessions_data.sort(
                key=lambda x: x["date_obj"] if x["date_obj"] else datetime.min,
                reverse=self.sort_reverse
            )
        elif self.sort_column == "duration":
            self.sessions_data.sort(
                key=lambda x: x["duration_seconds"],
                reverse=self.sort_reverse
            )
        elif self.sort_column == "size":
            self.sessions_data.sort(
                key=lambda x: x["size_bytes"],
                reverse=self.sort_reverse
            )
        else:  # session_id
            self.sessions_data.sort(
                key=lambda x: x["session_id"],
                reverse=self.sort_reverse
            )
        
        # Update column headers with sort indicators
        for col in ["session_id", "date", "duration", "size"]:
            text = col.replace("_", " ").title()
            if col == self.sort_column:
                indicator = " ▼" if self.sort_reverse else " ▲"
                self.tree.heading(col, text=text + indicator)
            else:
                self.tree.heading(col, text=text)
        
        # Clear and repopulate tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for session in self.sessions_data:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    session["session_id"],
                    session["date"],
                    session["duration"],
                    session["size"]
                )
            )
    
    def _on_select(self, event):
        """Handle session selection."""
        selection = self.tree.selection()
        if selection:
            self.export_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            
            # Display details
            item = self.tree.item(selection[0])
            session_id = item["values"][0]
            metadata = self.collector.get_session_metadata(session_id)
            
            if metadata:
                self._display_details(metadata)
        else:
            self.export_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
    
    def _display_details(self, metadata: dict):
        """Display session details.
        
        Args:
            metadata: Session metadata dictionary
        """
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = []
        details.append(f"Session ID: {metadata.get('session_id', 'N/A')}")
        details.append(f"Start: {metadata.get('start_time', 'N/A')}")
        details.append(f"End: {metadata.get('end_time', 'N/A')}")
        
        recorders = metadata.get('recorders_enabled', {})
        enabled = [k for k, v in recorders.items() if v and k != 'audio']  # Exclude audio
        details.append(f"Recorded: {', '.join(enabled)}")
        
        settings = metadata.get('settings', {})
        if settings:
            details.append(f"Quality: {settings.get('screen_quality', 'N/A')}")
        
        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state=tk.DISABLED)
    
    def _export_selected(self):
        """Export selected sessions."""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get selected session IDs
        session_ids = [self.tree.item(item)["values"][0] for item in selection]
        
        if len(session_ids) == 1:
            # Single session export
            session_id = session_ids[0]
            output_path = filedialog.asksaveasfilename(
                title="Export Session",
                defaultextension=".zip",
                filetypes=[("Zip files", "*.zip"), ("All files", "*.*")],
                initialfile=f"session_{session_id[:8]}.zip"
            )
            
            if output_path:
                result = self.exporter.export_session(session_id, output_path)
                if result:
                    messagebox.showinfo(
                        "Success",
                        f"Session exported successfully to:\n{output_path}"
                    )
                else:
                    messagebox.showerror("Error", "Failed to export session")
        else:
            # Multiple sessions export
            output_dir = filedialog.askdirectory(
                title="Select Export Directory"
            )
            
            if output_dir:
                success_count = 0
                for session_id in session_ids:
                    output_path = f"{output_dir}/session_{session_id[:8]}.zip"
                    if self.exporter.export_session(session_id, output_path):
                        success_count += 1
                
                if success_count == len(session_ids):
                    messagebox.showinfo(
                        "Success",
                        f"All {success_count} sessions exported successfully to:\n{output_dir}"
                    )
                else:
                    messagebox.showwarning(
                        "Partial Success",
                        f"Exported {success_count} of {len(session_ids)} sessions"
                    )
    
    def _export_all(self):
        """Export all sessions."""
        if not self.sessions_data:
            messagebox.showinfo("No Sessions", "No sessions to export")
            return
        
        output_dir = filedialog.askdirectory(
            title="Select Export Directory for All Sessions"
        )
        
        if output_dir:
            success_count = 0
            total = len(self.sessions_data)
            
            for session in self.sessions_data:
                session_id = session["session_id"]
                output_path = f"{output_dir}/session_{session_id[:8]}.zip"
                if self.exporter.export_session(session_id, output_path):
                    success_count += 1
            
            if success_count == total:
                messagebox.showinfo(
                    "Success",
                    f"All {success_count} sessions exported successfully to:\n{output_dir}"
                )
            else:
                messagebox.showwarning(
                    "Partial Success",
                    f"Exported {success_count} of {total} sessions"
                )
    
    def _delete_session(self):
        """Delete selected session."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        session_id = item["values"][0]
        
        # Confirm deletion
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete session:\n{session_id}?\n\nThis cannot be undone."
        ):
            success = self.collector.delete_session(session_id)
            if success:
                messagebox.showinfo("Success", "Session deleted successfully")
                self._load_sessions()
            else:
                messagebox.showerror("Error", "Failed to delete session")

