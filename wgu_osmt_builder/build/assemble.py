#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
assemble.py

Convert OSMT JSON → TTL, then merge all TTL into one ontology.

Defaults:
- JSON in:      wgu_osmt_builder/data/raw
- TTL out:      wgu_osmt_builder/data/out/ttl
- Merged TTL:   wgu_osmt_builder/data/out/ttl/skills.ttl

Behavior:
- Writes per-file TTLs into a staging folder: <ttl_out>/.partials
- Merges staged TTLs into skills.ttl
- Deletes the staging folder after a successful merge
"""

from __future__ import annotations

import os
import sys
import json
import shutil
from pathlib import Path

from rdflib import Graph

from wgu_osmt_builder.common.log import configure_logger
from wgu_osmt_builder.common.paths import RAW, TTL_OUT
from wgu_osmt_builder.build.json2ttl import TransformJSONtoTTL

logger = configure_logger(__name__)


def find_json_files(root_dir: Path) -> list[Path]:
    if not root_dir.exists():
        raise FileNotFoundError(f"Root directory not found: {root_dir}")
    return sorted(root_dir.rglob("*.json"))


def is_osmt_json(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict) and data.get("type") == "RichSkillDescriptor"
    except Exception:
        return False


def merge_ttls_to_single_ontology(src_dir: Path, merged_path: Path) -> None:
    g = Graph()
    ttl_files = sorted(src_dir.glob("*.ttl"))

    if not ttl_files:
        logger.warning(json.dumps({
            "json2ttl": "warn",
            "msg": "no ttl files to merge",
            "dir": str(src_dir)
        }))
        return

    for ttl_path in ttl_files:
        try:
            g.parse(ttl_path, format="turtle")
            logger.info(f"🧩 Merged TTL: {ttl_path}")
        except Exception as ex:
            logger.error(json.dumps({
                "json2ttl": "error",
                "msg": "failed to parse ttl",
                "src": str(ttl_path),
                "error": str(ex)
            }))

    merged_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(merged_path), format="turtle")
    logger.info(json.dumps({
        "json2ttl": "merged",
        "count": len(ttl_files),
        "dst": str(merged_path)
    }))


def process_directory(json_root: Path, ttl_out: Path, merged_path: Path) -> None:
    json_files = find_json_files(json_root)
    if not json_files:
        logger.info(f"⚠️ No JSON files found under {json_root}")
        return

    logger.info(f"📂 Found {len(json_files)} JSON file(s) under {json_root}")

    # Ensure final output dir exists; stage per-file TTLs under hidden subdir
    ttl_out.mkdir(parents=True, exist_ok=True)
    stage_dir = ttl_out / ".partials"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📦 Staging per-file TTLs in: {stage_dir}")

    converter = TransformJSONtoTTL(logger=logger)
    for json_path in json_files:
        if not is_osmt_json(json_path):
            logger.info(f"⏭️ Skip non-RSD JSON: {json_path}")
            continue

        dst_ttl = stage_dir / f"{json_path.stem}.ttl"
        logger.info(f"▶️ Converting: {json_path} → {dst_ttl}")
        try:
            converter.process(str(json_path), str(dst_ttl))
            logger.info(f"✅ Done: {json_path}")
        except Exception as ex:
            logger.error(json.dumps({
                "json2ttl": "error",
                "src": str(json_path),
                "error": str(ex),
            }))

    # Merge staged TTLs → single ontology
    merge_ttls_to_single_ontology(stage_dir, merged_path)

    # Remove intermediates; keep only merged
    try:
        shutil.rmtree(stage_dir)
        logger.info(f"🧹 Removed staging dir: {stage_dir}")
    except Exception as ex:
        logger.warning(f"⚠️ Could not remove staging dir {stage_dir}: {ex}")


def main() -> None:
    # Precedence: CLI > ENV > defaults from paths.py
    json_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.getenv("WGU_JSON_ROOT", RAW))
    ttl_out = Path(os.getenv("WGU_TTL_DIR", TTL_OUT))
    merged = Path(os.getenv("WGU_OWL_PATH", ttl_out / "skills.ttl"))
    process_directory(json_root, ttl_out, merged)


if __name__ == "__main__":
    main()
