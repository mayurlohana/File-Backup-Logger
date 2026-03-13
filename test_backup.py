"""
test_backup.py — Unit tests for File Backup Logger.

Tests cover:
    BackupManager  - plain copy, zip compression, versioning, error handling
    Logger         - success/failure entries, empty log
    ConfigManager  - defaults, set/persist, missing keys
"""

import os
import shutil
import tempfile
import unittest

from backup import BackupManager, BackupResult
from config import ConfigManager
from logger import Logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source(base: str) -> str:
    """Create a small test directory tree and return its path."""
    src = os.path.join(base, "source")
    os.makedirs(src)

    # Root-level files
    with open(os.path.join(src, "file1.txt"), "w") as fh:
        fh.write("Hello, World!")
    with open(os.path.join(src, "file2.txt"), "w") as fh:
        fh.write("Test data")

    # Nested sub-directory
    sub = os.path.join(src, "subdir")
    os.makedirs(sub)
    with open(os.path.join(sub, "file3.txt"), "w") as fh:
        fh.write("Nested file")

    return src   # 3 files total


# ---------------------------------------------------------------------------
# BackupManager tests
# ---------------------------------------------------------------------------

class TestBackupManagerPlainCopy(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.source = _make_source(self.tmp)
        self.dest = os.path.join(self.tmp, "destination")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_backup_succeeds(self):
        result = BackupManager(self.source, self.dest).run()
        self.assertTrue(result.success, msg=result.error)

    def test_file_count(self):
        result = BackupManager(self.source, self.dest).run()
        self.assertEqual(result.file_count, 3)

    def test_duration_positive(self):
        result = BackupManager(self.source, self.dest).run()
        self.assertGreater(result.duration, 0)

    def test_backup_path_exists(self):
        result = BackupManager(self.source, self.dest).run()
        self.assertTrue(os.path.exists(result.backup_path))

    def test_backup_name_contains_timestamp_and_version(self):
        result = BackupManager(self.source, self.dest).run()
        name = os.path.basename(result.backup_path)
        self.assertRegex(name, r"_backup_\d{4}-\d{2}-\d{2}_v\d+$")

    def test_first_backup_is_v1(self):
        result = BackupManager(self.source, self.dest).run()
        self.assertTrue(os.path.basename(result.backup_path).endswith("_v1"))


class TestBackupManagerZip(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.source = _make_source(self.tmp)
        self.dest = os.path.join(self.tmp, "destination")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_zip_backup_succeeds(self):
        result = BackupManager(self.source, self.dest, compress=True).run()
        self.assertTrue(result.success, msg=result.error)

    def test_zip_file_created(self):
        result = BackupManager(self.source, self.dest, compress=True).run()
        self.assertTrue(result.backup_path.endswith(".zip"))
        self.assertTrue(os.path.isfile(result.backup_path))

    def test_zip_file_count(self):
        result = BackupManager(self.source, self.dest, compress=True).run()
        self.assertEqual(result.file_count, 3)


class TestBackupManagerVersioning(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.source = _make_source(self.tmp)
        self.dest = os.path.join(self.tmp, "destination")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_version_increments_on_repeated_backup(self):
        r1 = BackupManager(self.source, self.dest).run()
        r2 = BackupManager(self.source, self.dest).run()
        r3 = BackupManager(self.source, self.dest).run()

        self.assertIn("_v1", os.path.basename(r1.backup_path))
        self.assertIn("_v2", os.path.basename(r2.backup_path))
        self.assertIn("_v3", os.path.basename(r3.backup_path))

    def test_mixed_zip_and_plain_versioning(self):
        r1 = BackupManager(self.source, self.dest, compress=False).run()
        r2 = BackupManager(self.source, self.dest, compress=True).run()

        self.assertIn("_v1", os.path.basename(r1.backup_path))
        self.assertIn("_v2", os.path.basename(r2.backup_path))


class TestBackupManagerErrorHandling(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dest = os.path.join(self.tmp, "destination")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_nonexistent_source(self):
        result = BackupManager("/this/path/does/not/exist", self.dest).run()
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)

    def test_source_is_a_file_not_directory(self):
        file_path = os.path.join(self.tmp, "not_a_dir.txt")
        with open(file_path, "w") as fh:
            fh.write("data")
        result = BackupManager(file_path, self.dest).run()
        self.assertFalse(result.success)

    def test_destination_inside_source(self):
        source = _make_source(self.tmp)
        dest_inside = os.path.join(source, "backups")
        result = BackupManager(source, dest_inside).run()
        self.assertFalse(result.success)
        self.assertIn("inside", result.error.lower())

    def test_source_equals_destination(self):
        source = _make_source(self.tmp)
        result = BackupManager(source, source).run()
        self.assertFalse(result.success)


# ---------------------------------------------------------------------------
# Logger tests
# ---------------------------------------------------------------------------

class TestLogger(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmp, "logs", "test.log")
        self.logger = Logger(self.log_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_log_returns_placeholder(self):
        self.assertEqual(self.logger.read(), "No log entries yet.")

    def test_success_entry_written(self):
        self.logger.log("/src", "/dst", True, file_count=5, duration=1.23)
        content = self.logger.read()
        self.assertIn("SUCCESS", content)
        self.assertIn("/src", content)
        self.assertIn("5", content)
        self.assertIn("1.23s", content)

    def test_failure_entry_written(self):
        self.logger.log("/src", "/dst", False, error="Permission denied")
        content = self.logger.read()
        self.assertIn("FAILED", content)
        self.assertIn("Permission denied", content)

    def test_multiple_entries_appended(self):
        self.logger.log("/src1", "/dst", True, file_count=1, duration=0.1)
        self.logger.log("/src2", "/dst", False, error="Oops")
        content = self.logger.read()
        self.assertIn("/src1", content)
        self.assertIn("/src2", content)

    def test_log_dir_created_automatically(self):
        self.assertTrue(os.path.isdir(os.path.dirname(self.log_path)))


# ---------------------------------------------------------------------------
# ConfigManager tests
# ---------------------------------------------------------------------------

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg_path = os.path.join(self.tmp, "config.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_default_values(self):
        cfg = ConfigManager(self.cfg_path)
        self.assertEqual(cfg.get("source_folder"), "")
        self.assertFalse(cfg.get("compress"))
        self.assertEqual(cfg.get("backup_interval_days"), 1)

    def test_set_persists_to_disk(self):
        cfg = ConfigManager(self.cfg_path)
        cfg.set("source_folder", "/my/source")

        cfg2 = ConfigManager(self.cfg_path)
        self.assertEqual(cfg2.get("source_folder"), "/my/source")

    def test_missing_key_returns_none(self):
        cfg = ConfigManager(self.cfg_path)
        self.assertIsNone(cfg.get("nonexistent_key"))

    def test_missing_key_returns_default(self):
        cfg = ConfigManager(self.cfg_path)
        self.assertEqual(cfg.get("nonexistent_key", "fallback"), "fallback")

    def test_new_keys_merged_with_defaults(self):
        cfg = ConfigManager(self.cfg_path)
        cfg.set("compress", True)

        # Simulate a new key being added in a future version
        cfg2 = ConfigManager(self.cfg_path)
        self.assertTrue(cfg2.get("compress"))
        self.assertEqual(cfg2.get("source_folder"), "")  # default still present


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
