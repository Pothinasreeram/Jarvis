"""
Maid Protocol Skill for J.A.R.V.I.S.
Handles voice requests to clean, organize, deduplicate, and archive files
across Desktop and Downloads.
"""

from system_layer.maid_controller import run_maid_protocol, find_duplicates, DOWNLOADS_DIR, DESKTOP_DIR

skill = {
    "name": "Maid Protocol Skill",
    "priority": 26,
}

TRIGGER_KEYWORDS = [
    "maid protocol",
    "clean up my downloads",
    "clean downloads",
    "clean my downloads",
    "organize downloads",
    "organize my downloads",
    "clean up desktop",
    "clean my desktop",
    "clean desktop",
    "organize desktop",
    "organize my desktop",
    "clean up both",
    "find duplicate files",
    "find duplicates",
    "check duplicates",
    "clean files",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if ("clean" in cmd or "organize" in cmd) and ("download" in cmd or "desktop" in cmd or "files" in cmd):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Just checking duplicates
    if "duplicate" in cmd and not ("clean" in cmd or "delete" in cmd):
        dl_dupes = find_duplicates(DOWNLOADS_DIR)
        dt_dupes = find_duplicates(DESKTOP_DIR)
        total = len(dl_dupes) + len(dt_dupes)
        if total == 0:
            return "I scanned your Downloads and Desktop, Sir. Zero duplicate files were detected."
        else:
            total_bytes = sum(s for _, _, s in dl_dupes + dt_dupes)
            mb = total_bytes / (1024 * 1024)
            return (
                f"I detected {total} duplicate files taking up approximately {mb:.1f} megabytes. "
                f"Say 'activate maid protocol' to safely quarantine them."
            )

    # 2. Specific Target
    if "desktop" in cmd and "download" not in cmd:
        return run_maid_protocol(target="desktop")
    elif "download" in cmd and "desktop" not in cmd:
        return run_maid_protocol(target="downloads")
    else:
        # Both or general maid protocol
        return run_maid_protocol(target="both")
