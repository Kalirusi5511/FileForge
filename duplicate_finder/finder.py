import hashlib
import os


def calculate_hash(filepath):
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def find_duplicates(directory):
    hashes = {}
    duplicates = []

    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)

            try:
                file_hash = calculate_hash(filepath)

                if file_hash in hashes:
                    hashes[file_hash].append(filepath)
                else:
                    hashes[file_hash] = [filepath]

            except Exception:
                continue

    for files in hashes.values():
        if len(files) > 1:
            duplicates.append(files)

    return duplicates
