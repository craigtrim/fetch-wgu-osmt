#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validate/alignments.py
Extract Alignment labels → newline-delimited text.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from rdflib import Graph, Namespace
from wgu_osmt_builder.common.paths import TTL_OUT, REPORTS

DEFAULT_TTL = TTL_OUT / "skills.ttl"
DEFAULT_OUT = REPORTS / "alignment-labels.txt"
NS = Namespace("https://w3id.org/wgu/osmt/skills#")

Q_TMPL = """
PREFIX :    <https://w3id.org/wgu/osmt/skills#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?lab WHERE {
  ?s rdf:type :Alignment .
  { ?s skos:prefLabel ?lab } {FILTER(LANGMATCHES(LANG(?lab), "%LANG%") || LANG(?lab) = "")}
  %ALT%
}
"""


def extract_alignment_labels(ttl_path: Path, out_path: Path, lang: str = "en", include_alt: bool = False) -> int:
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    alt_block = ""
    if include_alt:
        alt_block = """
        UNION {
          ?s rdf:type :Alignment .
          ?s skos:altLabel ?lab .
          FILTER(LANGMATCHES(LANG(?lab), "%LANG%") || LANG(?lab) = "")
        }
        """
    q = Q_TMPL.replace("%ALT%", alt_block).replace("%LANG%", lang)

    labels = sorted(str(row[0]) for row in g.query(q))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(labels) +
                        ("\n" if labels else ""), encoding="utf-8")
    return len(labels)


def _cli() -> None:
    ap = argparse.ArgumentParser(description="Extract Alignment labels")
    ap.add_argument("--ttl", type=Path, default=DEFAULT_TTL)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--alt", action="store_true", help="include skos:altLabel")
    args = ap.parse_args()
    n = extract_alignment_labels(
        args.ttl, args.out, lang=args.lang, include_alt=args.alt)
    print(f"✅ alignment labels: {n} → {args.out}")


if __name__ == "__main__":
    _cli()
