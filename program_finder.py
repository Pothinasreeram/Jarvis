"""
JARVIS Program Finder
Bridges legacy program lookup with the Universal App Controller.
"""

from system_layer.app_controller import find_app_path, get_installed_apps


def find_program(program_name):
    """Find program path using alias resolution and fuzzy matching."""
    match = find_app_path(program_name)
    if match:
        return match[1]
    return None


def load_program_database():
    """Return dictionary of installed apps."""
    return get_installed_apps()


def build_program_database():
    """Rebuild in-memory cache."""
    return get_installed_apps()