"""
gui.py — tkinter GUI for File Backup Logger.

Class:
    BackupGUI - Main application window. Provides folder selection,
                compression toggle, backup trigger, progress feedback,
                status display, and an embedded log viewer.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from backup import BackupManager
from config import ConfigManager
from logger import Logger


class BackupGUI:
    """
    Main window of the File Backup Logger application.

    Layout:
        - Source folder row  (entry + Browse button)
        - Destination folder row (entry + Browse button)
        - ZIP Compression checkbox
        - Start Backup button
        - Indeterminate progress bar
        - Status label
        - Backup Log viewer  (read-only ScrolledText + Refresh button)
    """

    APP_TITLE = "File Backup Logger"
    MIN_W, MIN_H = 640, 520

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.APP_TITLE)
        self.root.minsize(self.MIN_W, self.MIN_H)

        self.config = ConfigManager()
        self.logger = Logger("logs/backup.log")

        self._build_ui()
        self._load_prefs()
        self._refresh_log()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=14)
        main.grid(sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(7, weight=1)

        # --- Source folder ---
        ttk.Label(main, text="Source Folder:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.source_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.source_var).grid(
            row=0, column=1, sticky="ew", pady=5
        )
        ttk.Button(main, text="Browse…", command=self._select_source).grid(
            row=0, column=2, padx=(6, 0), pady=5
        )

        # --- Destination folder ---
        ttk.Label(main, text="Destination Folder:").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.dest_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.dest_var).grid(
            row=1, column=1, sticky="ew", pady=5
        )
        ttk.Button(main, text="Browse…", command=self._select_dest).grid(
            row=1, column=2, padx=(6, 0), pady=5
        )

        # --- ZIP compression toggle ---
        self.compress_var = tk.BooleanVar()
        ttk.Checkbutton(
            main,
            text="ZIP Compression",
            variable=self.compress_var,
            command=self._save_prefs,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 4))

        # --- Start Backup button ---
        self.backup_btn = ttk.Button(
            main, text="▶  Start Backup", command=self._start_backup
        )
        self.backup_btn.grid(row=3, column=0, columnspan=3, pady=10)

        # --- Progress bar ---
        self.pb = ttk.Progressbar(main, mode="indeterminate", length=300)
        self.pb.grid(row=4, column=0, columnspan=3, sticky="ew")

        # --- Status label (plain tk.Label so fg is easily settable) ---
        self.status_var = tk.StringVar(value="Ready.")
        self._status_lbl = tk.Label(
            main, textvariable=self.status_var, anchor="w", fg="gray"
        )
        self._status_lbl.grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=(4, 10)
        )

        # --- Log header row ---
        log_hdr = ttk.Frame(main)
        log_hdr.grid(row=6, column=0, columnspan=3, sticky="ew")
        ttk.Label(log_hdr, text="Backup Log:").pack(side="left")
        ttk.Button(log_hdr, text="Refresh", command=self._refresh_log).pack(
            side="right"
        )

        # --- Scrolled log text area ---
        self.log_box = scrolledtext.ScrolledText(
            main,
            height=12,
            state="disabled",
            wrap="word",
            font=("Courier", 10),
        )
        self.log_box.grid(
            row=7, column=0, columnspan=3, sticky="nsew", pady=4
        )

    # ------------------------------------------------------------------
    # Folder selection
    # ------------------------------------------------------------------

    def _select_source(self) -> None:
        path = filedialog.askdirectory(title="Select Source Folder")
        if path:
            self.source_var.set(path)
            self._save_prefs()

    def _select_dest(self) -> None:
        path = filedialog.askdirectory(title="Select Destination Folder")
        if path:
            self.dest_var.set(path)
            self._save_prefs()

    # ------------------------------------------------------------------
    # Backup execution
    # ------------------------------------------------------------------

    def _start_backup(self) -> None:
        source = self.source_var.get().strip()
        dest = self.dest_var.get().strip()

        if not source:
            messagebox.showwarning(self.APP_TITLE, "Please select a source folder.")
            return
        if not dest:
            messagebox.showwarning(
                self.APP_TITLE, "Please select a destination folder."
            )
            return

        self._save_prefs()
        self.backup_btn.config(state="disabled")
        self.pb.start(10)
        self._set_status("Backup in progress…", "blue")

        threading.Thread(
            target=self._run_backup,
            args=(source, dest, self.compress_var.get()),
            daemon=True,
        ).start()

    def _run_backup(self, source: str, dest: str, compress: bool) -> None:
        """Worker thread: performs backup and schedules UI update."""
        mgr = BackupManager(source, dest, compress)
        result = mgr.run()

        self.logger.log(
            source=source,
            destination=dest,
            status=result.success,
            file_count=result.file_count,
            duration=result.duration,
            error=result.error,
        )

        # Schedule UI update back on the main thread
        self.root.after(0, self._on_done, result)

    def _on_done(self, result) -> None:
        """Called on the main thread when the backup worker finishes."""
        self.pb.stop()
        self.backup_btn.config(state="normal")
        self._refresh_log()

        if result.success:
            self._set_status(
                f"Done — {result.file_count} file(s) backed up "
                f"in {result.duration:.2f}s",
                "green",
            )
            messagebox.showinfo(
                self.APP_TITLE,
                f"Backup completed successfully!\n\n"
                f"Files backed up : {result.file_count}\n"
                f"Duration        : {result.duration:.2f}s\n"
                f"Saved to        : {result.backup_path}",
            )
        else:
            self._set_status(f"Failed: {result.error}", "red")
            messagebox.showerror(
                self.APP_TITLE, f"Backup failed:\n{result.error}"
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg: str, color: str = "gray") -> None:
        self.status_var.set(msg)
        self._status_lbl.config(fg=color)

    def _refresh_log(self) -> None:
        content = self.logger.read()
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.insert("1.0", content)
        self.log_box.config(state="disabled")
        self.log_box.see("end")

    def _load_prefs(self) -> None:
        self.source_var.set(self.config.get("source_folder", ""))
        self.dest_var.set(self.config.get("destination_folder", ""))
        self.compress_var.set(self.config.get("compress", False))

    def _save_prefs(self) -> None:
        self.config.set("source_folder", self.source_var.get())
        self.config.set("destination_folder", self.dest_var.get())
        self.config.set("compress", self.compress_var.get())
