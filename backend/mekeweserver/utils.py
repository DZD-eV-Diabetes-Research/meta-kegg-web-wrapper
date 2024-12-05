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
    sum = 0
    for obj in dir.iterdir():
        if obj.is_file():
            sum += obj.stat().st_size
        elif obj.is_dir():
            sum += get_directory_size_bytes(obj)
    return sum
