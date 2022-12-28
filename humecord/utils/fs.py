"""
HumeCord/utils/fs

Handles basic filesystem operations.
Only really used for yaml, since everything
else is like 2 lines long.
"""

import yaml

def read_yaml(file):
    with open(file, "r") as f:
        return yaml.safe_load(f)