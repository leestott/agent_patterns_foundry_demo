"""
E2E demo validator — forwards to tests/test_demos.py.

Usage:
    python validate_demos.py            # run all 7 demo validations
    python validate_demos.py --help     # show tests/test_demos.py help

For the full unit + integration test suite run:
    python -m pytest tests/ -v

For unit tests only (no live Foundry service needed):
    python -m pytest tests/test_topology.py tests/test_event_bus.py \
        tests/test_model_config.py tests/test_api.py -v
"""
import subprocess
import sys

if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, "tests/test_demos.py"] + sys.argv[1:]).returncode)
