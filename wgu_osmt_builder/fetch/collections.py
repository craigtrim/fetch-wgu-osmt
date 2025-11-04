#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Scan a folder of WGU/OSMT CSV exports and fetch JSON for each.
Defaults:
  CSVs in:  wgu_osmt_builder/data/sources
  JSON out: wgu_osmt_builder/data/raw
"""

from __future__ import annotations

from pathlib import Path
from random import shuffle

from wgu_osmt_builder.common.log import configure_logger
from wgu_osmt_builder.common.csv_utils import find_csv_files, is_wgu_csv
from wgu_osmt_builder.common.paths import SOURCES, RAW
from wgu_osmt_builder.fetch.wgu import FetchWGUData

logger = configure_logger(__name__)


def process_directory(root_dir: str | Path, out_dir: str | Path | None = None) -> None:
    src_dir = Path(root_dir)
    dst_dir = Path(out_dir) if out_dir else RAW
    csv_files = find_csv_files(str(src_dir))
    if not csv_files:
        logger.info(f"⚠️ No CSV files found under {src_dir}")
        return

    logger.info(f"📂 Found {len(csv_files)} CSV file(s) under {src_dir}")
    shuffle(csv_files)

    for csv_path in csv_files:
        if not is_wgu_csv(csv_path):
            logger.info(f"⏭️ Skip non-WGU CSV: {csv_path}")
            continue

        logger.info(f"▶️ Processing WGU CSV: {csv_path}")
        FetchWGUData(csv_path=str(csv_path), output_root=str(dst_dir)).process()
        logger.info(f"✅ Done: {csv_path}")


def main() -> None:
    # Default to data/sources → data/raw
    process_directory(SOURCES, RAW)


if __name__ == "__main__":
    main()
