import os

def file_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0
