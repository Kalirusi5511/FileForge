import zipfile
from pathlib import Path


def extract(path, destination):
    destination = Path(destination)

    with zipfile.ZipFile(path, "r") as archive:
        archive.extractall(destination)

    return destination