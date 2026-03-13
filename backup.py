"""
backup.py — Core backup logic for File Backup Logger.

Classes:
    BackupResult  - Data class holding the outcome of a backup run.
    BackupManager - Handles copying / zipping a source directory to a
                    versioned backup inside the destination folder.
"""

import os
import re
import shutil
import time
import zipfile
from datetime import datetime


class BackupResult:
    """Holds the result of a single backup operation."""

    def __init__(
        self,
        success: bool,
        backup_path: str,
        file_count: int,
        duration: float,
        error: str = None,
    ):
        self.success = success
        self.backup_path = backup_path
        self.file_count = file_count
        self.duration = duration
        self.error = error


class BackupManager:
    """
    Manages backup operations with automatic versioning, optional ZIP
    compression, and robust error handling.

    Backup folder/file names follow the pattern:
        <source_name>_backup_<YYYY-MM-DD>_v<N>
        <source_name>_backup_<YYYY-MM-DD>_v<N>.zip  (compressed)
    """

    def __init__(self, source: str, destination: str, compress: bool = False):
        self.source = os.path.abspath(source)
        self.destination = os.path.abspath(destination)
        self.compress = compress

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_next_version(self) -> int:
        """Scan destination for existing backups of this source and return
        the next incremental version number."""
        if not os.path.exists(self.destination):
            return 1

        source_name = re.escape(os.path.basename(self.source))
        pattern = re.compile(
            rf"^{source_name}_backup_\d{{4}}-\d{{2}}-\d{{2}}_v(\d+)(\.zip)?$"
        )

        max_version = 0
        try:
            for entry in os.listdir(self.destination):
                m = pattern.match(entry)
                if m:
                    max_version = max(max_version, int(m.group(1)))
        except PermissionError:
            pass  # Will be caught later when we try to write

        return max_version + 1

    def _make_backup_name(self, version: int) -> str:
        """Build the backup folder/file base name."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        source_name = os.path.basename(self.source)
        return f"{source_name}_backup_{timestamp}_v{version}"

    @staticmethod
    def _count_files(path: str) -> int:
        """Recursively count all files under *path*."""
        count = 0
        for _, _, files in os.walk(path):
            count += len(files)
        return count

    # ------------------------------------------------------------------
    # Copy / zip implementations
    # ------------------------------------------------------------------

    def _copy(self, dest_path: str) -> int:
        """Plain directory copy. Returns file count."""
        shutil.copytree(self.source, dest_path)
        return self._count_files(dest_path)

    def _zip(self, zip_path: str) -> int:
        """Compress source into a ZIP archive. Returns file count."""
        count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(self.source):
                for name in files:
                    full_path = os.path.join(root, name)
                    # Preserve relative structure inside the zip
                    arc_name = os.path.relpath(
                        full_path, os.path.dirname(self.source)
                    )
                    zf.write(full_path, arc_name)
                    count += 1
        return count

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> BackupResult:
        """Execute the backup operation and return a BackupResult."""
        start = time.time()

        # --- Input validation ---
        if not os.path.exists(self.source):
            return BackupResult(
                False, "", 0, 0,
                f"Source does not exist: {self.source}"
            )

        if not os.path.isdir(self.source):
            return BackupResult(
                False, "", 0, 0,
                f"Source is not a directory: {self.source}"
            )

        if not os.access(self.source, os.R_OK):
            return BackupResult(
                False, "", 0, 0,
                f"Permission denied (read): {self.source}"
            )

        # Prevent backing up into itself or a subdirectory of source
        src_real = os.path.realpath(self.source)
        dst_real = os.path.realpath(self.destination)
        if dst_real == src_real or dst_real.startswith(src_real + os.sep):
            return BackupResult(
                False, "", 0, 0,
                "Destination cannot be inside or equal to the source folder."
            )

        # Create destination directory
        try:
            os.makedirs(self.destination, exist_ok=True)
        except PermissionError:
            return BackupResult(
                False, "", 0, 0,
                f"Permission denied (write): {self.destination}"
            )
        except OSError as exc:
            return BackupResult(
                False, "", 0, 0,
                f"Cannot create destination directory: {exc}"
            )

        if not os.access(self.destination, os.W_OK):
            return BackupResult(
                False, "", 0, 0,
                f"Permission denied (write): {self.destination}"
            )

        # --- Execute backup ---
        version = self._get_next_version()
        backup_name = self._make_backup_name(version)

        try:
            if self.compress:
                backup_path = os.path.join(
                    self.destination, backup_name + ".zip"
                )
                file_count = self._zip(backup_path)
            else:
                backup_path = os.path.join(self.destination, backup_name)
                file_count = self._copy(backup_path)

        except PermissionError as exc:
            return BackupResult(
                False, "", 0, time.time() - start,
                f"Permission denied during backup: {exc}"
            )
        except OSError as exc:
            return BackupResult(
                False, "", 0, time.time() - start,
                f"OS error during backup: {exc}"
            )
        except Exception as exc:  # pylint: disable=broad-except
            return BackupResult(
                False, "", 0, time.time() - start,
                f"Unexpected error: {exc}"
            )

        return BackupResult(True, backup_path, file_count, time.time() - start)
