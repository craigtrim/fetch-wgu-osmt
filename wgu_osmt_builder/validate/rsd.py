#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validate/rsd.py
Extract English SKOS prefLabels from :RichSkillDescriptor nodes.

IN:  wgu_osmt_builder/data/out/ttl/skills.ttl
OUT: wgu_osmt_builder/data/out/reports/rsd-pref-labels.txt
"""

from __future__ import annotations
import argparse
from pathlib import Path
from rdflib import Graph
from wgu_osmt_builder.common.paths import TTL_OUT, REPORTS

DEFAULT_TTL = TTL_OUT / "skills.ttl"
DEFAULT_OUT = REPORTS / "rsd-pref-labels.txt"

Q = """
PREFIX :    <https://w3id.org/wgu/osmt/skills#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?lab WHERE {
  ?s rdf:type :RichSkillDescriptor ;
     skos:prefLabel ?lab .
  FILTER( LANGMATCHES(LANG(?lab), "%LANG%") || LANG(?lab) = "" )
}
"""


def extract_rsd_pref_labels(ttl_path: Path, out_path: Path, lang: str = "en") -> int:
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    labels = sorted(str(row[0]) for row in g.query(Q.replace("%LANG%", lang)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(labels) +
                        ("\n" if labels else ""), encoding="utf-8")
    return len(labels)


def _cli() -> None:
    ap = argparse.ArgumentParser(description="Extract RSD SKOS prefLabels")
    ap.add_argument("--ttl", type=Path, default=DEFAULT_TTL)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    n = extract_rsd_pref_labels(args.ttl, args.out, lang=args.lang)
    print(f"✅ rsd prefLabels: {n} → {args.out}")


if __name__ == "__main__":
    _cli()
