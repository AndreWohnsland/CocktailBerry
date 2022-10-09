from pathlib import Path


def importer(file_path: Path, factor: float = 1.0):
    if not file_path.exists():
        print("This file does not exists!")
        return
    if not file_path.is_file():
        print("The path does not lead to a file!")
        return
    print(file_path, factor)
