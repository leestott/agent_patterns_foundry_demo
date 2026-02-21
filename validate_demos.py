"""
Shim — validation has moved to tests/test_demos.py.

This file is kept for backwards compatibility. For the full test suite run:
    python -m pytest tests/ -v
For the E2E demo validation report:
    python tests/test_demos.py
"""
import subprocess
import sys

if __name__ == "__main__":
    print("[info] validate_demos.py has moved to tests/test_demos.py")
    sys.exit(subprocess.run([sys.executable, "tests/test_demos.py"] + sys.argv[1:]).returncode)
