# wgu_osmt_builder/graph/export.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from rdflib import Graph, URIRef, Literal

from wgu_osmt_builder.common.log import configure_logger
from wgu_osmt_builder.common.paths import TTL_OUT, GRAPH
from wgu_osmt_builder.graph.build.schema import (
    # namespaces, classes, props
    RDF,
    CLS_RSD, CLS_KEYWORD, CLS_CATEGORY, CLS_STANDARD, CLS_OCCUPATION, CLS_COLLECTION, CLS_ALIGNMENT,
    P_PREF_LABEL, P_STATUS, P_IDENTIFIER, P_TITLE, P_NOTATION, P_CREATED, P_ISSUED, P_MODIFIED,
    # headers, helpers, rels
    HDR_RSD, HDR_KEYWORD, HDR_CATEGORY, HDR_STANDARD, HDR_OCCUPATION, HDR_COLLECTION, HDR_ALIGNMENT, HDR_REL,
    localname, REL_SPECS,
)

logger = configure_logger(__name__)


# -------------------- IO helpers --------------------

def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    logger.info(f"📝 wrote {len(rows):,} rows → {path}")


def _first_label(g: Graph, s: URIRef, lang: str = "en") -> str:
    # prefer matching language or no language
    best: str | None = None
    for _, _, o in g.triples((s, P_PREF_LABEL, None)):
        if isinstance(o, Literal):
            if o.language and o.language.lower() == lang:
                return str(o)
            if o.language is None and best is None:
                best = str(o)
    return best or ""


def _first_literal(g: Graph, s: URIRef, p: URIRef) -> str:
    for _, _, o in g.triples((s, p, None)):
        if isinstance(o, Literal):
            return str(o)
    return ""


# -------------------- Node extractors --------------------

def _collect_rsd_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_RSD)):
        nid = localname(s)
        row = [
            nid,
            "RichSkillDescriptor",
            _first_label(g, s),
            _first_literal(g, s, P_IDENTIFIER),
            _first_literal(g, s, P_STATUS),
            _first_literal(g, s, P_CREATED),
            _first_literal(g, s, P_ISSUED),
            _first_literal(g, s, P_MODIFIED),
        ]
        rows.append(row)
    rows.sort(key=lambda r: r[0])
    return rows


def _collect_keyword_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_KEYWORD)):
        rows.append([localname(s), "Keyword", _first_label(g, s)])
    rows.sort(key=lambda r: r[0])
    return rows


def _collect_category_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_CATEGORY)):
        rows.append([localname(s), "Category", _first_label(g, s)])
    rows.sort(key=lambda r: r[0])
    return rows


def _collect_standard_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_STANDARD)):
        rows.append([
            localname(s), "Standard", _first_label(g, s),
            _first_literal(g, s, P_NOTATION)
        ])
    rows.sort(key=lambda r: r[0])
    return rows


def _collect_occupation_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_OCCUPATION)):
        rows.append([
            localname(s), "Occupation", _first_label(g, s),
            _first_literal(g, s, P_IDENTIFIER) or localname(
                s).removeprefix("bls-")
        ])
    rows.sort(key=lambda r: r[0])
    return rows


def _collect_collection_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_COLLECTION)):
        rows.append([
            localname(s), "Collection",
            _first_literal(g, s, P_TITLE),
            _first_literal(g, s, P_IDENTIFIER),
        ])
    rows.sort(key=lambda r: r[0])
    return rows


def _collect_alignment_nodes(g: Graph) -> list[list[str]]:
    rows: list[list[str]] = []
    for s, _, _ in g.triples((None, RDF.type, CLS_ALIGNMENT)):
        rows.append([
            localname(s), "Alignment",
            _first_label(g, s),
            _first_literal(g, s, P_IDENTIFIER),
        ])
    rows.sort(key=lambda r: r[0])
    return rows


# -------------------- Relationship extractors --------------------

def _collect_relationships(g: Graph) -> dict[str, list[list[str]]]:
    """
    Returns map: filename → rows
    """
    out: dict[str, list[list[str]]] = {
        "rels_rsd_hasKeyword.csv": [],
        "rels_rsd_hasCategory.csv": [],
        "rels_rsd_hasStandard.csv": [],
        "rels_rsd_hasOccupation.csv": [],
        "rels_rsd_inCollection.csv": [],
        "rels_rsd_hasAlignment.csv": [],
        "rels_occupation_partOf.csv": [],
    }

    name_map = {
        ("RichSkillDescriptor", "HAS_KEYWORD"):    "rels_rsd_hasKeyword.csv",
        ("RichSkillDescriptor", "HAS_CATEGORY"):   "rels_rsd_hasCategory.csv",
        ("RichSkillDescriptor", "HAS_STANDARD"):   "rels_rsd_hasStandard.csv",
        ("RichSkillDescriptor", "HAS_OCCUPATION"): "rels_rsd_hasOccupation.csv",
        ("RichSkillDescriptor", "IN_COLLECTION"):  "rels_rsd_inCollection.csv",
        ("RichSkillDescriptor", "HAS_ALIGNMENT"):  "rels_rsd_hasAlignment.csv",
        ("Occupation",          "PART_OF"):        "rels_occupation_partOf.csv",
    }

    for spec in REL_SPECS:
        # Correct pattern: predicate must be in the P-slot
        for s, _, o in g.triples((None, spec.pred, None)):
            if not isinstance(s, URIRef) or not isinstance(o, URIRef):
                continue
            # ensure s has expected type via rdf:type
            typed = any(True for _ in g.triples((s, RDF.type, spec.src_cls)))
            if not typed:
                continue
            start = localname(s)
            end = localname(o)
            key = ("Occupation", spec.rel_type) if spec.src_cls == CLS_OCCUPATION else (
                "RichSkillDescriptor", spec.rel_type)
            fname = name_map[key]
            out[fname].append([start, end, spec.rel_type])

    # sort deterministically
    for k in out:
        out[k].sort(key=lambda r: (r[0], r[1], r[2]))
    return out


# -------------------- Public API --------------------

def export_neo_csvs(ttl_path: Path | None = None, out_dir: Path | None = None) -> None:
    """
    Read skills.ttl and emit Neo4j bulk-import CSVs.
    """
    ttl = Path(ttl_path or (TTL_OUT / "skills.ttl"))
    dst = Path(out_dir or GRAPH)
    if not ttl.exists():
        raise FileNotFoundError(f"TTL not found: {ttl}")

    g = Graph()
    g.parse(str(ttl), format="turtle")
    logger.info(f"📦 parsed TTL: {ttl}")

    # nodes
    _write_csv(dst / "nodes_rsd.csv",
               HDR_RSD,        _collect_rsd_nodes(g))
    _write_csv(dst / "nodes_keyword.csv",
               HDR_KEYWORD,    _collect_keyword_nodes(g))
    _write_csv(dst / "nodes_category.csv",
               HDR_CATEGORY,   _collect_category_nodes(g))
    _write_csv(dst / "nodes_standard.csv",
               HDR_STANDARD,   _collect_standard_nodes(g))
    _write_csv(dst / "nodes_occupation.csv",
               HDR_OCCUPATION, _collect_occupation_nodes(g))
    _write_csv(dst / "nodes_collection.csv",
               HDR_COLLECTION, _collect_collection_nodes(g))
    _write_csv(dst / "nodes_alignment.csv",
               HDR_ALIGNMENT,  _collect_alignment_nodes(g))

    # relationships
    rels = _collect_relationships(g)
    for fname, rows in rels.items():
        _write_csv(dst / fname, HDR_REL, rows)

    logger.info(f"✅ graph export complete → {dst}")
