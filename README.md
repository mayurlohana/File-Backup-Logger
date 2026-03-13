#File Backup Logger

## Description
A program that backs up files and directories with versioning, logs the operations locally, and includes a GUI. Alternatively, the program can be written in python if you're more comfortable working with it.

## Getting Started
1. Clone this repository or download the files.
2. Install required packages if necessary.
3. Run the `main.py` file to get started.

Keep in mind that the code must be written in OOP.

## Tasks
- Research how to copy folders in Python using `shutil`. Create initial project folder and file structure.
- Implement basic folder selection (manually or via `input()`). Write code to copy folder contents to a backup location.
- Add timestamp and version of the program is backuping an software directory to backup folder names (e.g., backup_2025-05-01_v227-3-3).
- Add error handling (e.g., non-existent folder, permission denied). Start writing a simple .log file (backup time, status).
- Clean up code. Create `backup.py` and move reusable functions there. Test with multiple folders and large files.
- Add ZIP compression to backups using `zipfile`. Let user choose between zipped or plain copy.
- Improve the log format. Add file count and backup duration.
- Add tkinter GUI to select source/destination folders and trigger backup.
- Add config file (e.g., .json) to store user preferences (folders, backup interval).
- Final testing. Create README with instructions and screenshots. Submit as Git repo.

## Estimated time to work 2 weeks
