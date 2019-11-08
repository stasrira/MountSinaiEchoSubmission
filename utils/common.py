from pathlib import Path

def get_project_root():
    # Returns project root folder.
    return Path(__file__).parent.parent

def file_exists(fn):
    try:
        with open(fn, "r"):
            return 1
    except IOError:
        return 0