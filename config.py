"""
config.py — JSON-based user preference manager for File Backup Logger.

Class:
    ConfigManager - Loads, reads, updates, and persists user preferences
                    in a config.json file.
"""

import json
import os

_DEFAULTS: dict = {
    "source_folder": "",
    "destination_folder": "",
    "compress": False,
    "backup_interval_days": 1,
}


class ConfigManager:
    """
    Manages user preferences stored in a JSON config file.

    On first run the file is created with sensible defaults.
    Any stored keys are merged with defaults so new keys added in
    future versions are always available.
    """

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._data: dict = {}
        self._load()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load config from disk, falling back to defaults on error."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                # Merge: stored values win, but defaults fill missing keys
                self._data = {**_DEFAULTS, **stored}
            except (json.JSONDecodeError, OSError):
                self._data = _DEFAULTS.copy()
        else:
            self._data = _DEFAULTS.copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist current config to disk."""
        with open(self.config_path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=4)

    def get(self, key: str, default=None):
        """Return the value for *key*, or *default* if not found."""
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        """Update *key* to *value* and immediately save to disk."""
        self._data[key] = value
        self.save()
