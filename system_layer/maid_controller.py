"""
Autonomous Maid Protocol for J.A.R.V.I.S.
Intelligent Desktop & Downloads Auto-Organizer, Deduplicator, and Stale File Archiver.
"""

import os
import shutil
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Target paths
USER_DIR = os.environ.get("USERPROFILE", "")
DOWNLOADS_DIR = os.path.join(USER_DIR, "Downloads")
DESKTOP_DIR = os.path.join(USER_DIR, "OneDrive", "Desktop") if os.path.exists(os.path.join(USER_DIR, "OneDrive", "Desktop")) else os.path.join(USER_DIR, "Desktop")

# Extension Mapping
EXTENSIONS_MAP = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".epub", ".rtf", ".odt"],
    "Installers": [".exe", ".msi", ".iso", ".dmg", ".pkg"],
    "Media": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mkv", ".mp3", ".wav", ".mov", ".flac", ".avi", ".svg"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code_Data": [".py", ".js", ".ts", ".html", ".css", ".json", ".sql", ".ipynb", ".cpp", ".java", ".xml", ".yaml", ".yml"],
}

# Protected files and folders that must NEVER be moved
PROTECTED_EXTENSIONS = [".lnk", ".ini", ".url", ".sys", ".tmp"]
PROTECTED_NAMES = ["desktop.ini", "thumbs.db", ".ds_store"]
ORGANIZED_FOLDERS = set(EXTENSIONS_MAP.keys()) | {"Duplicates", "Stale_Archive"}


def _get_file_hash(filepath: str, block_size: int = 65536) -> str:
    """Calculate MD5 hash of file content."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
    except Exception:
        return ""


def find_duplicates(folder_path: str) -> List[Tuple[str, str, int]]:
    """
    Find exact duplicate files in the target directory using size + MD5 hashing.
    Returns: list of (original_path, duplicate_path, file_size_bytes)
    """
    if not os.path.exists(folder_path):
        return []

    size_map: Dict[int, List[str]] = {}
    duplicates: List[Tuple[str, str, int]] = []

    try:
        for entry in os.scandir(folder_path):
            if not entry.is_file():
                continue
            name = entry.name.lower()
            if any(name.endswith(ext) for ext in PROTECTED_EXTENSIONS) or name in PROTECTED_NAMES:
                continue

            try:
                size = entry.stat().st_size
                if size > 0:
                    size_map.setdefault(size, []).append(entry.path)
            except Exception:
                continue

        # Check hashes for identical sizes
        for size, filepaths in size_map.items():
            if len(filepaths) > 1:
                hash_map: Dict[str, str] = {}
                for path in filepaths:
                    h = _get_file_hash(path)
                    if not h:
                        continue
                    if h in hash_map:
                        duplicates.append((hash_map[h], path, size))
                    else:
                        hash_map[h] = path

    except Exception as e:
        print(f"[MAID DUPLICATE SCAN ERROR]: {e}")

    return duplicates


def organize_directory(folder_path: str, archive_stale: bool = True, quarantine_dupes: bool = True) -> Dict[str, Any]:
    """
    Execute Maid Protocol on a single directory.
    - Categorizes loose files into clean subdirectories.
    - Quarantines duplicate files into Duplicates/
    - Moves files older than 30 days into Stale_Archive/
    """
    if not os.path.exists(folder_path):
        return {"success": False, "error": f"Folder not found: {folder_path}"}

    stats = {
        "files_moved": 0,
        "categories_populated": set(),
        "duplicates_quarantined": 0,
        "space_saved_bytes": 0,
        "stale_archived": 0,
    }

    # 1. Deduplication
    if quarantine_dupes:
        dupes = find_duplicates(folder_path)
        if dupes:
            dupes_dir = os.path.join(folder_path, "Duplicates")
            os.makedirs(dupes_dir, exist_ok=True)
            for orig, dupe, size in dupes:
                try:
                    dest = os.path.join(dupes_dir, os.path.basename(dupe))
                    # Prevent collision
                    if os.path.exists(dest):
                        base, ext = os.path.splitext(os.path.basename(dupe))
                        dest = os.path.join(dupes_dir, f"{base}_{int(time.time())}{ext}")
                    shutil.move(dupe, dest)
                    stats["duplicates_quarantined"] += 1
                    stats["space_saved_bytes"] += size
                except Exception as e:
                    print(f"[MAID DUPE MOVE ERROR]: {e}")

    # 2. Categorization & Stale Archiving
    now = time.time()
    stale_threshold = 30 * 86400  # 30 days

    for entry in list(os.scandir(folder_path)):
        if entry.is_dir():
            continue

        name = entry.name
        name_lower = name.lower()
        filepath = entry.path

        # Ignore protected files
        if any(name_lower.endswith(ext) for ext in PROTECTED_EXTENSIONS) or name_lower in PROTECTED_NAMES:
            continue

        _, ext = os.path.splitext(name_lower)
        target_category = None

        for cat, ext_list in EXTENSIONS_MAP.items():
            if ext in ext_list:
                target_category = cat
                break

        if not target_category:
            continue

        try:
            mtime = entry.stat().st_mtime
            is_stale = (now - mtime) > stale_threshold

            if archive_stale and is_stale:
                # Move to dated archive
                date_str = datetime.fromtimestamp(mtime).strftime("%Y_%m")
                target_dir = os.path.join(folder_path, "Stale_Archive", date_str)
                stats["stale_archived"] += 1
            else:
                target_dir = os.path.join(folder_path, target_category)

            os.makedirs(target_dir, exist_ok=True)
            dest_file = os.path.join(target_dir, name)

            # Prevent overwriting
            if os.path.exists(dest_file):
                base, ext_orig = os.path.splitext(name)
                dest_file = os.path.join(target_dir, f"{base}_{int(time.time())}{ext_orig}")

            shutil.move(filepath, dest_file)
            stats["files_moved"] += 1
            stats["categories_populated"].add(target_category)

        except (PermissionError, OSError) as pe:
            # File may be open in another application
            continue
        except Exception as e:
            print(f"[MAID ORGANIZE ERROR]: {e}")

    stats["categories_populated"] = list(stats["categories_populated"])
    return stats


def run_maid_protocol(target: str = "downloads") -> str:
    """
    Top-level API for voice command execution.
    - target: 'downloads', 'desktop', or 'both'
    """
    target = target.lower().strip()
    total_moved = 0
    total_dupes = 0
    total_space = 0
    all_cats = set()

    folders_to_clean = []
    if "desktop" in target or target == "both":
        folders_to_clean.append(("Desktop", DESKTOP_DIR))
    if "download" in target or target == "both":
        folders_to_clean.append(("Downloads", DOWNLOADS_DIR))

    if not folders_to_clean:
        folders_to_clean = [("Downloads", DOWNLOADS_DIR)]

    for label, path in folders_to_clean:
        res = organize_directory(path)
        total_moved += res.get("files_moved", 0)
        total_dupes += res.get("duplicates_quarantined", 0)
        total_space += res.get("space_saved_bytes", 0)
        all_cats.update(res.get("categories_populated", []))

    mb_saved = total_space / (1024 * 1024)
    if mb_saved >= 1024:
        space_str = f"{mb_saved / 1024.0:.1f} gigabytes"
    elif mb_saved > 0:
        space_str = f"{mb_saved:.1f} megabytes"
    else:
        space_str = "zero bytes"

    if total_moved == 0 and total_dupes == 0:
        return "Maid Protocol inspected your workspace, Sir. Everything is already organized and clean."

    cats_str = ", ".join(sorted(all_cats)) if all_cats else "standard categories"
    return (
        f"Maid Protocol complete, Sir. Organized {total_moved} files across {cats_str}. "
        f"Quarantined {total_dupes} duplicate files, reclaiming {space_str} of storage."
    )
