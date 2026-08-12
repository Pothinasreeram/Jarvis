import os

from system_layer.file_indexer import (
    build_index,
    search_index
)

# Build index once when imported
build_index()


def open_file(path):
    os.startfile(path)


def find_file(name):

    matches = search_index(name)

    return matches

def open_match(match):

    os.startfile(match["path"])

    return f"Opening {os.path.basename(match['path'])}"