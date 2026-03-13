# File Backup Logger

A desktop application written in Python that backs up folders with **automatic versioning**, optional **ZIP compression**, structured **operation logging**, and a clean **tkinter GUI**. Built entirely with Object-Oriented Programming principles and Python's standard library — no third-party packages required.

---

## Table of Contents

- [Why We Built This](#why-we-built-this)
- [Features](#features)
- [Project Structure](#project-structure)
- [Architecture & Design Decisions](#architecture--design-decisions)
- [Getting Started](#getting-started)
- [Using the Application](#using-the-application)
- [Configuration File](#configuration-file)
- [Log File Format](#log-file-format)
- [Running the Tests](#running-the-tests)
- [Backup Naming Convention](#backup-naming-convention)
- [Error Handling](#error-handling)

---

## Why We Built This

Manual file backups are error-prone — people forget to do them, overwrite previous versions, and have no record of what was backed up or when. This project solves those problems by:

- **Automating the copy/compress step** so users don't have to manage it by hand.
- **Versioning every backup automatically** so previous snapshots are never overwritten.
- **Logging every operation** with a timestamp, file count, and duration so there is always an audit trail.
- **Persisting user preferences** in a config file so the same folders don't need to be re-entered every session.
- **Providing a GUI** so the tool is accessible to users who are not comfortable with the command line.

The project was also a learning exercise in structuring a Python application using **OOP**, separating concerns into focused classes, and writing a comprehensive unit-test suite.

---

## Features

| Feature | Details |
|---|---|
| Plain folder backup | Uses `shutil.copytree` to copy the full directory tree |
| ZIP compression | Uses `zipfile` with `ZIP_DEFLATED` to create a compressed archive |
| Automatic versioning | Backup names increment (`_v1`, `_v2`, …) — nothing is ever overwritten |
| Timestamped names | Every backup includes the date (`YYYY-MM-DD`) in its name |
| Structured log file | Records timestamp, source, destination, status, file count, and duration |
| JSON config file | Remembers last-used folders and compression preference across sessions |
| tkinter GUI | Browse buttons, compression toggle, progress bar, embedded log viewer |
| Robust error handling | Guards against missing source, permission errors, destination-inside-source, etc. |
| 25 unit tests | Full test coverage for `BackupManager`, `Logger`, and `ConfigManager` |

---

## Project Structure

```
File-Backup-Logger/
├── main.py          # Entry point — creates the Tk root window and launches the GUI
├── gui.py           # BackupGUI class — all tkinter widgets and user interaction
├── backup.py        # BackupManager + BackupResult classes — core backup logic
├── logger.py        # Logger class — writes structured entries to the log file
├── config.py        # ConfigManager class — reads/writes config.json
├── test_backup.py   # 25 unit tests (unittest, no external dependencies)
├── logs/
│   └── backup.log   # Created automatically on first backup
├── config.json      # Created automatically on first run (gitignored)
└── README.md
```

---

## Architecture & Design Decisions

### `BackupManager` (`backup.py`)
Owns everything related to performing a backup. It validates inputs, determines the next version number by scanning the destination directory, builds the versioned name, and then either calls `shutil.copytree` (plain copy) or writes a `zipfile.ZipFile` (compressed). It returns a `BackupResult` data object so the caller never needs to catch exceptions — errors are surfaced as structured values.

**Why a separate result object?** It decouples the backup logic from the UI. The GUI, tests, and any future CLI frontend all consume the same `BackupResult` without caring how the backup was performed.

### `Logger` (`logger.py`)
A single-responsibility class that appends formatted entries to a plain-text `.log` file. Keeping logging separate from `BackupManager` means the backup logic has no knowledge of how results are recorded — they can be logged to a file, a database, or a remote service without touching backup code.

### `ConfigManager` (`config.py`)
Wraps a `config.json` file with a simple `get` / `set` API. Default values are merged with whatever is on disk, so adding new preference keys in a future version never breaks existing config files.

### `BackupGUI` (`gui.py`)
Runs the backup on a **background thread** (`threading.Thread`) so the UI never freezes during long copy operations. Results are scheduled back onto the main thread via `root.after(0, callback)` — the correct pattern for tkinter thread safety.

### `main.py`
A minimal entry point that creates the `Tk` root window, instantiates `BackupGUI`, and starts the event loop. Keeping it separate makes the application easy to test headlessly (import `backup`, `logger`, `config` without triggering the GUI).

---

## Getting Started

### Prerequisites

- Python 3.8 or later
- `tkinter` — included with the standard Python installer on Windows and macOS. On some Linux distributions you may need to install it separately:

```bash
# Ubuntu / Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

No third-party packages are required. Everything else (`shutil`, `zipfile`, `json`, `threading`, `unittest`) is part of the Python standard library.

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/mayurlohana/File-Backup-Logger.git
cd File-Backup-Logger

# 2. (Optional) Check out the feature branch
git checkout file-backup-logger

# 3. Launch the application
python main.py
```

---

## Using the Application

### Step-by-step

1. **Launch** — run `python main.py` from the project directory. The main window opens.

2. **Select Source Folder** — click **Browse…** next to *Source Folder* and pick the folder you want to back up.

3. **Select Destination Folder** — click **Browse…** next to *Destination Folder* and choose where backups should be saved. This can be an external drive, a different disk, or any local directory.

4. **Choose backup type** — tick **ZIP Compression** if you want a compressed `.zip` archive. Leave it unticked for a plain folder copy.

5. **Start Backup** — click **▶ Start Backup**. The progress bar animates while the backup runs in the background.

6. **Review the result** — a dialog confirms success (with file count and duration) or explains any error. The **Backup Log** panel at the bottom updates automatically.

7. **View logs** — click **Refresh** in the log panel at any time to reload the latest entries from `logs/backup.log`.

> Your folder paths and compression preference are saved automatically to `config.json` and restored the next time you open the app.

### GUI Overview

```
┌─────────────────────────────────────────────────────┐
│  Source Folder:      [/path/to/source      ] [Browse]│
│  Destination Folder: [/path/to/destination ] [Browse]│
│  ☐ ZIP Compression                                   │
│                  [ ▶ Start Backup ]                  │
│  ══════════════ progress bar ═══════════════         │
│  Status: Done — 42 file(s) backed up in 0.85s        │
│  Backup Log:                          [Refresh]      │
│  ┌───────────────────────────────────────────────┐   │
│  │ ============================================================ │
│  │ Timestamp   : 2026-03-13 14:22:01             │   │
│  │ Source      : /Users/you/my-project           │   │
│  │ Destination : /Volumes/Backup                 │   │
│  │ Status      : SUCCESS                         │   │
│  │ Files       : 42                              │   │
│  │ Duration    : 0.85s                           │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Configuration File

`config.json` is created automatically in the project directory on first run. You can edit it manually or let the GUI manage it.

```json
{
	"source_folder": "/Users/you/my-project",
	"destination_folder": "/Volumes/Backup",
	"compress": false,
	"backup_interval_days": 1
}
```

| Key | Type | Description |
|---|---|---|
| `source_folder` | string | Last-used source folder path |
| `destination_folder` | string | Last-used destination folder path |
| `compress` | boolean | Whether ZIP compression is enabled |
| `backup_interval_days` | integer | Reserved for future scheduled-backup feature |

> `config.json` is listed in `.gitignore` and will not be committed to version control.

---

## Log File Format

Every backup operation appends an entry to `logs/backup.log`. The `logs/` directory is created automatically.

```
============================================================
Timestamp   : 2026-03-13 14:22:01
Source      : /Users/you/my-project
Destination : /Volumes/Backup
Status      : SUCCESS
Files       : 42
Duration    : 0.85s

============================================================
Timestamp   : 2026-03-13 14:35:10
Source      : /Users/you/missing-folder
Destination : /Volumes/Backup
Status      : FAILED
Files       : 0
Duration    : 0.00s
Error       : Source does not exist: /Users/you/missing-folder

```

> `logs/` is listed in `.gitignore` and will not be committed to version control.

---

## Running the Tests

The test suite uses Python's built-in `unittest` module — no additional packages needed.

```bash
python test_backup.py -v
```

Expected output (25 tests, all passing):

```
test_destination_inside_source ... ok
test_nonexistent_source ... ok
test_source_equals_destination ... ok
test_source_is_a_file_not_directory ... ok
test_backup_name_contains_timestamp_and_version ... ok
test_backup_path_exists ... ok
test_backup_succeeds ... ok
test_duration_positive ... ok
test_file_count ... ok
test_first_backup_is_v1 ... ok
test_mixed_zip_and_plain_versioning ... ok
test_version_increments_on_repeated_backup ... ok
test_zip_backup_succeeds ... ok
test_zip_file_count ... ok
test_zip_file_created ... ok
test_default_values ... ok
test_missing_key_returns_default ... ok
test_missing_key_returns_none ... ok
test_new_keys_merged_with_defaults ... ok
test_set_persists_to_disk ... ok
test_empty_log_returns_placeholder ... ok
test_failure_entry_written ... ok
test_log_dir_created_automatically ... ok
test_multiple_entries_appended ... ok
test_success_entry_written ... ok

----------------------------------------------------------------------
Ran 25 tests in 0.098s

OK
```

---

## Backup Naming Convention

Backups are named using the following pattern:

```
<source_folder_name>_backup_<YYYY-MM-DD>_v<N>
<source_folder_name>_backup_<YYYY-MM-DD>_v<N>.zip   ← compressed
```

**Examples:**

```
my-project_backup_2026-03-13_v1/
my-project_backup_2026-03-13_v2/
my-project_backup_2026-03-13_v3.zip
```

The version number is determined at runtime by scanning the destination folder for existing backups of the same source. This guarantees backups are never silently overwritten, regardless of how many times you back up on the same day.

---

## Error Handling

The application guards against the following error conditions and surfaces a clear message in both the GUI dialog and the log file:

| Condition | Message |
|---|---|
| Source folder does not exist | `Source does not exist: <path>` |
| Source path is a file, not a directory | `Source is not a directory: <path>` |
| No read permission on source | `Permission denied (read): <path>` |
| No write permission on destination | `Permission denied (write): <path>` |
| Destination is inside the source folder | `Destination cannot be inside or equal to the source folder.` |
| Destination equals source | Same as above |
| OS-level errors during copy | `OS error during backup: <details>` |
