#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Sanity check for report generation prerequisites.

Fail if:
- rdflib is not importable
- skills.ttl is missing at the expected path
- reports directory is not writable
"""

from pathlib import Path
import os

from wgu_osmt_builder.common.paths import TTL_OUT, REPORTS


def test_report_prereqs_exist_and_writable(tmp_path):
    # 1) Dependency: rdflib import
    try:
        import rdflib  # noqa: F401
    except Exception as ex:
        raise AssertionError(f"rdflib not importable: {ex}")

    # 2) Input: merged TTL must exist
    ttl_path: Path = TTL_OUT / "skills.ttl"
    assert ttl_path.exists() and ttl_path.is_file(), f"Missing merged TTL: {ttl_path}"

    # 3) Output dir: reports must exist or be creatable and writable
    reports_dir: Path = REPORTS
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        raise AssertionError(f"Cannot create reports dir {reports_dir}: {ex}")

    # 4) Write check: create and remove a temp file inside reports
    probe = reports_dir / ".write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        assert probe.exists(), f"Write probe not created in {reports_dir}"
    finally:
        try:
            if probe.exists():
                probe.unlink()
        except OSError:
            # If we cannot remove it, at least signal path
            raise AssertionError(f"Probe file left behind: {probe}")

    # 5) Environment echo for debugging (non-fatal)
    print(f"TTL_OUT={TTL_OUT}")
    print(f"REPORTS={REPORTS}")
    print(f"skills.ttl size={ttl_path.stat().st_size} bytes")
