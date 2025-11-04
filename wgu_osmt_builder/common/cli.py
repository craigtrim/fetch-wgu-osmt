#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unified CLI for WGU OSMT builder.

Subcommands:
  fetch     → pull JSON from WGU/OSMT URLs listed in CSVs
  build     → convert JSON → TTL and merge to skills.ttl
  validate  → extract label reports from skills.ttl
  graph     → export Neo4j bulk-import CSVs from skills.ttl

Defaults use wgu_osmt_builder.common.paths.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from wgu_osmt_builder.common.log import configure_logger
from wgu_osmt_builder.common.paths import RAW, TTL_OUT, REPORTS
from wgu_osmt_builder.common.config import PROXIES_PATH

# fetch
from wgu_osmt_builder.fetch.wgu import FetchWGUData
from wgu_osmt_builder.fetch.collections import process_directory as fetch_collections

# build
from wgu_osmt_builder.build.assemble import process_directory as build_process

# validate
from wgu_osmt_builder.validate.alignments import extract_alignment_labels
from wgu_osmt_builder.validate.bls import extract_bls_pref_labels
from wgu_osmt_builder.validate.keywords import extract_keyword_labels
from wgu_osmt_builder.validate.rsd import extract_rsd_pref_labels

# graph export
from wgu_osmt_builder.graph.build.export import export_neo_csvs
from wgu_osmt_builder.common.paths import TTL_OUT as _TTL_DEFAULT  # explicit for help text
try:
    from wgu_osmt_builder.common.paths import GRAPH as GRAPH_OUT_DEFAULT  # optional path
except Exception:
    GRAPH_OUT_DEFAULT = Path("data/out/graph")

logger = configure_logger(__name__)


# ----------------------------- fetch -----------------------------
def _cmd_fetch(args: argparse.Namespace) -> int:
    if args.dir and args.csv:
        logger.error("Provide either --dir or --csv, not both.")
        return 2

    out_dir = Path(args.out or RAW)
    proxies_path = Path(args.proxies or PROXIES_PATH)

    if args.dir:
        src_dir = Path(args.dir)
        if not src_dir.exists():
            logger.error(f"CSV directory not found: {src_dir}")
            return 2
        fetch_collections(str(src_dir))
        return 0

    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            logger.error(f"CSV not found: {csv_path}")
            return 2
        FetchWGUData(
            csv_path=str(csv_path),
            output_root=str(out_dir),
            proxies_path=str(proxies_path),
            pause_seconds=args.pause,
        ).process()
        return 0

    logger.error("Nothing to do. Use --dir for a CSV folder or --csv for a single CSV.")
    return 2


# ----------------------------- build -----------------------------
def _cmd_build(args: argparse.Namespace) -> int:
    json_root = Path(args.json_root or RAW)
    ttl_out = Path(args.ttl_out or TTL_OUT)
    merged = Path(args.merged or (ttl_out / "skills.ttl"))

    build_process(json_root, ttl_out, merged)
    return 0


# --------------------------- validate ----------------------------
def _cmd_validate(args: argparse.Namespace) -> int:
    ttl_path = Path(args.ttl or (TTL_OUT / "skills.ttl"))
    out_dir = Path(args.out_dir or REPORTS)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected: list[str] = []
    if args.all or not any([args.alignments, args.bls, args.keywords, args.rsd]):
        selected = ["alignments", "bls", "keywords", "rsd"]
    else:
        if args.alignments:
            selected.append("alignments")
        if args.bls:
            selected.append("bls")
        if args.keywords:
            selected.append("keywords")
        if args.rsd:
            selected.append("rsd")

    totals: dict[str, int] = {}

    if "alignments" in selected:
        dst = out_dir / "alignment-labels.txt"
        totals["alignments"] = extract_alignment_labels(
            ttl_path, dst, lang=args.lang, include_alt=args.alt
        )

    if "bls" in selected:
        dst = out_dir / "bls-labels.txt"
        totals["bls"] = extract_bls_pref_labels(ttl_path, dst, lang=args.lang)

    if "keywords" in selected:
        dst = out_dir / "keyword-labels.txt"
        totals["keywords"] = extract_keyword_labels(ttl_path, dst, lang=args.lang)

    if "rsd" in selected:
        dst = out_dir / "rsd-pref-labels.txt"
        totals["rsd"] = extract_rsd_pref_labels(ttl_path, dst, lang=args.lang)

    logger.info(f"reports: {totals}")
    return 0


# ---------------------------- graph ------------------------------
def _cmd_graph(args: argparse.Namespace) -> int:
    ttl_path = Path(args.ttl or (TTL_OUT / "skills.ttl"))
    out_dir = Path(args.out_dir or GRAPH_OUT_DEFAULT)
    export_neo_csvs(ttl_path=ttl_path, out_dir=out_dir)
    return 0


# ----------------------------- parser ----------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wgu-osmt-builder", description="WGU OSMT builder CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    # fetch
    pf = sub.add_parser("fetch", help="Fetch JSON skills from CSV exports")
    pf.add_argument("--dir", help="Directory of CSV files to scan")
    pf.add_argument("--csv", help="Single CSV file to process")
    pf.add_argument("--out", help=f"Output directory for JSON (default: {RAW})")
    pf.add_argument("--proxies", help=f"Path to proxies.txt (default: {PROXIES_PATH})")
    pf.add_argument("--pause", type=float, default=0.5, help="Pause between requests in seconds")
    pf.set_defaults(func=_cmd_fetch)

    # build
    pb = sub.add_parser("build", help="Convert JSON → TTL and merge to skills.ttl")
    pb.add_argument("--json-root", help=f"Root dir of JSON inputs (default: {RAW})")
    pb.add_argument("--ttl-out", help=f"Directory for per-file TTL outputs (default: {TTL_OUT})")
    pb.add_argument("--merged", help="Path to merged skills.ttl (default: <ttl-out>/skills.ttl)")
    pb.set_defaults(func=_cmd_build)

    # validate
    pv = sub.add_parser("validate", help="Generate label reports from skills.ttl")
    pv.add_argument("--ttl", help=f"Path to skills.ttl (default: {_TTL_DEFAULT / 'skills.ttl'})")
    pv.add_argument("--out-dir", help=f"Reports directory (default: {REPORTS})")
    pv.add_argument("--lang", default="en", help="Language filter for labels")
    pv.add_argument("--alt", action="store_true", help="Include skos:altLabel where supported")
    pv.add_argument("--alignments", action="store_true", help="Only alignment labels")
    pv.add_argument("--bls", action="store_true", help="Only BLS labels")
    pv.add_argument("--keywords", action="store_true", help="Only keyword labels")
    pv.add_argument("--rsd", action="store_true", help="Only RSD labels")
    pv.add_argument("--all", action="store_true", help="Run all reports")
    pv.set_defaults(func=_cmd_validate)

    # graph
    pg = sub.add_parser("graph", help="Export Neo4j bulk-import CSVs from skills.ttl")
    pg.add_argument("--ttl", help=f"Path to skills.ttl (default: {_TTL_DEFAULT / 'skills.ttl'})")
    pg.add_argument("--out-dir", help=f"Graph CSV output dir (default: {GRAPH_OUT_DEFAULT})")
    pg.set_defaults(func=_cmd_graph)

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
