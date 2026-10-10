"""Command line: python -m germany_masters {scrape,build,all}"""

import argparse
import sys

from . import __version__, dashboard, scrape


def main(argv=None) -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="germany_masters", description=__doc__)
    parser.add_argument("command", choices=["scrape", "build", "all"],
                        help="scrape: download DAAD data to data/; build: render docs/index.html; all: both")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    if args.command in ("scrape", "all"):
        scrape.run()
    if args.command in ("build", "all"):
        dashboard.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
