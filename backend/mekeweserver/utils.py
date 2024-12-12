import os
from typing import List
from pathlib import Path


def bytes_humanreadable(num: int, suffix: str = "B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def get_directory_size_bytes(dir: Path) -> int:
    if dir.is_file():
        return dir.stat().st_size
    sum = 0
    for obj in dir.iterdir():
        if obj.is_file():
            sum += obj.stat().st_size
        elif obj.is_dir():
            sum += get_directory_size_bytes(obj)
    return sum


def count_files_in_dir_tree(dir: Path) -> int:
    if dir.is_file():
        return 1
    sum = 0
    for obj in dir.iterdir():
        if obj.is_file():
            sum += 1
        elif obj.is_dir():
            sum += count_files_in_dir_tree(obj)
    return sum


def get_module_root_dir() -> Path:
    return Path(__file__).parent
