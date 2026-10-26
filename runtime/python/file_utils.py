"""exteraGram `file_utils` on the AyuGram iOS runtime.

Directories live in the app's sandbox, under the root the host passes at
startup. Paths outside the sandbox fail like any other inaccessible path.
"""
import os

import _ayu_java

_root = os.path.join(os.path.expanduser("~"), ".ayu-python-plugins")


def _configure(root):
    global _root
    _root = root


def _dir(name):
    path = os.path.join(_root, name)
    os.makedirs(path, exist_ok=True)
    return path


def get_plugins_dir():
    return _dir("plugins")


def get_cache_dir():
    return _dir("cache")


def get_files_dir():
    return _dir("files")


def get_images_dir():
    return _dir("images")


def get_videos_dir():
    return _dir("videos")


def get_audios_dir():
    return _dir("audios")


def get_documents_dir():
    return _dir("documents")


def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)


def list_dir(path, recursive=False, include_files=True, include_dirs=False, extensions=None):
    result = []
    extensions = tuple(e.lower() if e.startswith(".") else "." + e.lower() for e in (extensions or []))
    if recursive:
        walker = os.walk(path)
    else:
        top = next(os.walk(path), None)
        walker = [top] if top else []
    for base, dirs, files in walker:
        if include_dirs:
            result.extend(os.path.join(base, d) for d in dirs)
        if include_files:
            result.extend(os.path.join(base, f) for f in files if not extensions or f.lower().endswith(extensions))
    return result


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def read_file(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


def write_file_bytes(path, content):
    with open(path, "wb") as handle:
        handle.write(content)


def read_file_bytes(path):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def delete_file(path):
    try:
        os.remove(path)
        return True
    except OSError:
        return False


class FilesController:
    @staticmethod
    def register(file_info):
        _ayu_java.note("unsupportedSdk", "FilesController.register")
        return ""

    @staticmethod
    def unregister(ext, secret):
        return None
