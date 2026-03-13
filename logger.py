"""
logger.py — Structured file logger for File Backup Logger.

Class:
    Logger - Appends formatted backup log entries to a .log file and
             provides a method to read the full log content.
"""

import os
from datetime import datetime


class Logger:
    """
    Writes structured backup log entries to a plain-text log file.

    Each entry records:
        - Timestamp
        - Source / Destination paths
        - Status (SUCCESS / FAILED)
        - File count
        - Duration
        - Error message (if any)
    """

    _SEP = "=" * 60

    def __init__(self, log_path: str = "logs/backup.log"):
        self.log_path = log_path
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    def log(
        self,
        source: str,
        destination: str,
        status: bool,
        file_count: int = 0,
        duration: float = 0.0,
        error: str = None,
    ) -> None:
        """Append one formatted log entry to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            self._SEP,
            f"Timestamp   : {timestamp}",
            f"Source      : {source}",
            f"Destination : {destination}",
            f"Status      : {'SUCCESS' if status else 'FAILED'}",
            f"Files       : {file_count}",
            f"Duration    : {duration:.2f}s",
        ]
        if error:
            lines.append(f"Error       : {error}")
        lines.append("")  # blank line after each entry

        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def read(self) -> str:
        """Return the full log file content, or a placeholder if empty."""
        if not os.path.exists(self.log_path):
            return "No log entries yet."
        with open(self.log_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        return content if content.strip() else "No log entries yet."
