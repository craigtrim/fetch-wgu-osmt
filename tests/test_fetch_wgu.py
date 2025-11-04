# tests/test_fetch_wgu.py
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import csv
from pathlib import Path
import pytest

from wgu_osmt_builder.fetch import wgu as wgu_mod
from wgu_osmt_builder.fetch.wgu import FetchWGUData

@pytest.mark.network
def test_fetch_single_skill_json_only(tmp_path: Path):
    # Point the code at a stable JSON host
    wgu_mod._OSMT_HOST = "https://jsonplaceholder.typicode.com"

    # One row CSV with Canonical URL on that host
    csv_path = tmp_path / "skills.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Skill Name", "Canonical URL"])
        writer.writeheader()
        writer.writerow({
            "Skill Name": "Demo",
            "Canonical URL": "https://jsonplaceholder.typicode.com/todos/1"
        })

    out_dir = tmp_path / "out"
    fetcher = FetchWGUData(
        csv_path=str(csv_path),
        output_root=str(out_dir),
        proxies_path=str(tmp_path / "no-proxies.txt"),  # non-existent → direct
        pause_seconds=0.0,
    )
    fetcher.process()

    # Expect filename from final path segment: '1.json'
    out_file = out_dir / "1.json"
    assert out_file.exists(), "Expected output JSON not written"

    # Sanity: JSON parses and has an 'id' field
    data = out_file.read_text(encoding="utf-8")
    assert '"id"' in data
