# tests/test_graph_prereqs.py
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Sanity check for graph export prerequisites.

Fail if:
- rdflib is not importable
- skills.ttl is missing at the expected path
- graph output directory is not writable
"""

from pathlib import Path

from wgu_osmt_builder.common.paths import TTL_OUT, GRAPH


def test_graph_prereqs_exist_and_writable():
    # 1) Dependency: rdflib import
    try:
        import rdflib  # noqa: F401
    except Exception as ex:
        raise AssertionError(f"rdflib not importable: {ex}")

    # 2) Input: merged TTL must exist
    ttl_path: Path = TTL_OUT / "skills.ttl"
    assert ttl_path.exists() and ttl_path.is_file(), f"Missing merged TTL: {ttl_path}"

    # 3) Output dir: GRAPH must exist or be creatable and writable
    graph_dir: Path = GRAPH
    try:
        graph_dir.mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        raise AssertionError(f"Cannot create graph dir {graph_dir}: {ex}")

    # 4) Write probe inside GRAPH
    probe = graph_dir / ".write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        assert probe.exists(), f"Write probe not created in {graph_dir}"
    finally:
        if probe.exists():
            try:
                probe.unlink()
            except OSError as ex:
                raise AssertionError(f"Probe file left behind: {probe} ({ex})")

    # 5) Debug echoes
    print(f"TTL_OUT={TTL_OUT}")
    print(f"GRAPH={GRAPH}")
    print(f"skills.ttl size={ttl_path.stat().st_size} bytes")
