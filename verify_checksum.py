import hashlib
import os
import sys

# ExecStartPre=/var/www/mon_projet/.venv/bin/python /var/www/mon_projet/verify_checksum.py

REFERENCE_HASH = "COPY_HASH_HERE"

IGNORED_PATHS = {
    '__pycache__', '.git', '.venv', 'media', 'static',
    'db.sqlite3', '.env', 'verify_checksum.py'
}


def get_project_checksum(directory="."):
    sha256 = hashlib.sha256()

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORED_PATHS]

        for file in sorted(files):
            if file.endswith(('.pyc', '.log')) or file in IGNORED_PATHS:
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'rb') as f:
                    sha256.update(file_path.encode('utf-8'))
                    while chunk := f.read(65536):
                        sha256.update(chunk)
            except Exception:
                pass

    return sha256.hexdigest()


if __name__ == "__main__":
    current_hash = get_project_checksum()

    if REFERENCE_HASH == "COPY_HASH_HERE":
        print("--- FIRST RUN ---")
        print(f"Your reference checksum is: {current_hash}")
        print("Copy this value and paste it into the REFERENCE_HASH variable at the top of this script.")
        sys.exit(1)

    if current_hash == REFERENCE_HASH:
        print("Checksum valid. Start authorized.")
        sys.exit(0)
    else:
        print("ERROR: Invalid checksum!")
        print(f"Expected: {REFERENCE_HASH}")
        print(f"Got     : {current_hash}")
        sys.exit(1)