# wgu_osmt_builder/common/csv_utils.py
import csv
from pathlib import Path


def find_csv_files(root_dir: str | Path) -> list[str]:
    base = Path(root_dir)
    if not base.exists():
        raise FileNotFoundError(f"Root directory not found: {root_dir}")
    return sorted(str(p) for p in base.rglob("*.csv"))


def is_wgu_csv(path: str | Path) -> bool:
    p = Path(path)
    try:
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            return "Canonical URL" in header
    except Exception:
        return False
