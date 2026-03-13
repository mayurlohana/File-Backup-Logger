"""
main.py — Entry point for File Backup Logger.

Run this file to launch the application:
    python main.py
"""

import tkinter as tk

from gui import BackupGUI


def main() -> None:
    """Create the root Tk window and start the application."""
    root = tk.Tk()
    BackupGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
