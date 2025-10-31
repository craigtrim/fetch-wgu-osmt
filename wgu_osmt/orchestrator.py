#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
orchestrator.py

Walk a directory, find CSVs, and run the WGU fetcher on each.
Only processes CSVs that look like WGU skill exports (must contain "Canonical URL").
"""

import os
import sys
import csv
from pathlib import Path

from wgu_osmt.dto import configure_logger
from wgu_osmt.svc import FetchWGUData  # the class you just built


logger = configure_logger(__name__)


def find_csv_files(root_dir: str) -> list[str]:
    """Return all .csv files under root_dir (recursive)."""
    base = Path(root_dir)
    if not base.exists():
        raise FileNotFoundError(f"Root directory not found: {root_dir}")

    csv_paths: list[str] = []
    for path in base.rglob("*.csv"):
        csv_paths.append(str(path))
    return sorted(csv_paths)


def is_wgu_csv(path: str) -> bool:
    """
    Heuristic: CSV must have a header and contain "Canonical URL".
    Skip tiny or malformed files.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            return "Canonical URL" in header
    except Exception:
        return False


def process_directory(root_dir: str):
    csv_files = find_csv_files(root_dir)
    if not csv_files:
        logger.info(f"⚠️ No CSV files found under {root_dir}")
        return

    logger.info(f"📂 Found {len(csv_files)} CSV file(s) under {root_dir}")

    for csv_path in csv_files:
        if not is_wgu_csv(csv_path):
            logger.info(f"⏭️ Skip non-WGU CSV: {csv_path}")
            continue

        logger.info(f"▶️ Processing WGU CSV: {csv_path}")
        fetcher = FetchWGUData(csv_path=csv_path)
        fetcher.process()
        logger.info(f"✅ Done: {csv_path}")


def main():
    # priority: CLI arg > env > default
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.environ.get("WGU_CSV_ROOT", "resources/input")
    process_directory(root_dir)


if __name__ == "__main__":
    main()
