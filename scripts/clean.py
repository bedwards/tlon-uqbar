import shutil
from pathlib import Path

def main():
    patterns = ["__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build"]
    for pattern in patterns:
        for path in Path(".").rglob(pattern):
            print(f"Removing {path}")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

if __name__ == "__main__":
    main()

