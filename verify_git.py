import subprocess
import sys

# ExecStartPre=/var/www/mon_projet/.venv/bin/python /var/www/mon_projet/verify_git.py

if __name__ == "__main__":
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            print("ERROR: Local changes detected on the server! Blocked startup.")
            print(result.stdout)
            sys.exit(1)
        else:
            print("Git status clean. Start authorized.")
            sys.exit(0)

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Git command failed. {e}")
        sys.exit(1)