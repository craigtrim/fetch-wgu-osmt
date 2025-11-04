#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validate/bls.py
Extract English SKOS prefLabels for BLS nodes (IRIs whose localname starts with 'bls-').

IN:  wgu_osmt_builder/data/out/ttl/skills.ttl
OUT: wgu_osmt_builder/data/out/reports/bls-labels.txt
"""

from __future__ import annotations
import argparse
from pathlib import Path
from rdflib import Graph

from wgu_osmt_builder.common.paths import TTL_OUT, REPORTS

DEFAULT_TTL = TTL_OUT / "skills.ttl"
DEFAULT_OUT = REPORTS / "bls-labels.txt"
NS_BASE = "https://w3id.org/wgu/osmt/skills#"

Q_TMPL = """
PREFIX :    <https://w3id.org/wgu/osmt/skills#>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>

SELECT DISTINCT ?lab WHERE {
  ?s skos:prefLabel ?lab .
  FILTER( LANGMATCHES(LANG(?lab), "%LANG%") || LANG(?lab) = "" )
  FILTER( STRSTARTS(STR(?s), "%NS%bls-") )
}
"""

def extract_bls_pref_labels(ttl_path: Path, out_path: Path, lang: str = "en") -> int:
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    q = Q_TMPL.replace("%LANG%", lang).replace("%NS%", NS_BASE)
    labels = sorted(str(row[0]) for row in g.query(q))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")
    return len(labels)

def _cli() -> None:
    ap = argparse.ArgumentParser(description="Extract BLS prefLabels from skills.ttl")
    ap.add_argument("--ttl", type=Path, default=DEFAULT_TTL, help="Path to skills.ttl")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output txt path")
    ap.add_argument("--lang", default="en", help="Language tag to keep (default: en)")
    args = ap.parse_args()
    n = extract_bls_pref_labels(args.ttl, args.out, lang=args.lang)
    print(f"✅ BLS labels: {n} → {args.out}")

if __name__ == "__main__":
    _cli()
