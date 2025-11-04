#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validate/keywords.py
Extract English SKOS prefLabels from :Keyword nodes, clean, filter, dedupe, sort.

IN:  wgu_osmt_builder/data/out/ttl/skills.ttl
OUT: wgu_osmt_builder/data/out/reports/keyword-labels.txt
"""

from __future__ import annotations
import argparse
import re
import unicodedata
from pathlib import Path

from rdflib import Graph

from wgu_osmt_builder.common.paths import TTL_OUT, REPORTS

DEFAULT_TTL = TTL_OUT / "skills.ttl"
DEFAULT_OUT = REPORTS / "keyword-labels.txt"

Q = """
PREFIX :    <https://w3id.org/wgu/osmt/skills#>
PREFIX skos:<http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?lab WHERE {
  ?s a :Keyword ;
     skos:prefLabel ?lab .
  FILTER( LANGMATCHES(LANG(?lab), "%LANG%") || LANG(?lab) = "" )
}
"""

_ws_re = re.compile(r"\s+")
_num_only_re = re.compile(r"^\d+(?:\.\d+)?$")   # 10344, 10344.1
_digit_code_re = re.compile(r"^\d+[-.].*$")     # 11-0000, 12-lead, 1404.22
_wgusid_re = re.compile(r"^wgusid\b", re.IGNORECASE)


def clean_label(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower().strip()
    s = _ws_re.sub(" ", s)
    s = s.rstrip(".")
    s = _ws_re.sub(" ", s).strip()
    return s


def valid_label(s: str) -> bool:
    if len(s) < 3:
        return False
    if _num_only_re.match(s):
        return False
    if _digit_code_re.match(s):
        return False
    if _wgusid_re.match(s):
        return False
    return True


def extract_keyword_labels(ttl_path: Path, out_path: Path, lang: str = "en") -> int:
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    labels = []
    q = Q.replace("%LANG%", lang)
    for (lab,) in g.query(q):
        t = clean_label(str(lab))
        if valid_label(t):
            labels.append(t)

    uniq_sorted = sorted(dict.fromkeys(labels))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(uniq_sorted) +
                        ("\n" if uniq_sorted else ""), encoding="utf-8")
    return len(uniq_sorted)


def _cli() -> None:
    ap = argparse.ArgumentParser(
        description="Extract cleaned Keyword labels from skills.ttl")
    ap.add_argument("--ttl", type=Path, default=DEFAULT_TTL)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()
    n = extract_keyword_labels(args.ttl, args.out, lang=args.lang)
    print(f"✅ keyword labels: {n} → {args.out}")


if __name__ == "__main__":
    _cli()
