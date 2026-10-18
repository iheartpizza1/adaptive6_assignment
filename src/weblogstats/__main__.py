"""Allows ``python -m weblogstats``."""

import sys

from weblogstats.cli import main

if __name__ == "__main__":
    sys.exit(main())
