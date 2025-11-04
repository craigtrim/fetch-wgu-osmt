
# wgu_osmt_builder/graph/schema.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rdflib import Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS, XSD  # re-export

# Base namespace used in the TTL header
BASE = Namespace("https://w3id.org/wgu/osmt/skills#")

# Classes
CLS_RSD = BASE.RichSkillDescriptor
CLS_KEYWORD = BASE.Keyword
CLS_CATEGORY = BASE.Category
CLS_STANDARD = BASE.Standard
CLS_OCCUPATION = BASE.Occupation
CLS_COLLECTION = BASE.Collection
CLS_ALIGNMENT = BASE.Alignment

# Object properties
P_HAS_KEYWORD = BASE.hasKeyword
P_HAS_CATEGORY = BASE.hasCategory
P_HAS_STANDARD = BASE.hasStandard
P_HAS_OCCUPATION = BASE.hasOccupation
P_IN_COLLECTION = BASE.inCollection
P_HAS_ALIGNMENT = BASE.hasAlignment
P_PART_OF = BASE.partOf

# Common data properties we read
P_PREF_LABEL = SKOS.prefLabel
P_ALT_LABEL = SKOS.altLabel
P_NOTATION = SKOS.notation
P_STATUS = BASE.status
P_IDENTIFIER = DCTERMS.identifier
P_TITLE = DCTERMS.title
P_SOURCE = DCTERMS.source
P_CREATED = DCTERMS.created
P_ISSUED = DCTERMS.issued
P_MODIFIED = DCTERMS.modified
P_DEFINITION = SKOS.definition

# ------------ Neo4j CSV headers ------------

# Node headers
HDR_RSD = [
    ":ID",
    ":LABEL",
    "prefLabel",
    "identifier",
    "status",
    "created:datetime",
    "issued:datetime",
    "modified:datetime",
]

HDR_KEYWORD = [":ID", ":LABEL", "prefLabel"]
HDR_CATEGORY = [":ID", ":LABEL", "prefLabel"]
HDR_STANDARD = [":ID", ":LABEL", "prefLabel", "notation"]
HDR_OCCUPATION = [":ID", ":LABEL", "prefLabel", "code"]
HDR_COLLECTION = [":ID", ":LABEL", "title", "identifier"]
HDR_ALIGNMENT = [":ID", ":LABEL", "prefLabel", "identifier"]

# Relationship headers
HDR_REL = [":START_ID", ":END_ID", ":TYPE"]

# ------------ Helpers ------------


def localname(u: URIRef) -> str:
    s = str(u)
    for sep in ("#", "/", ":"):
        if sep in s:
            s = s.rsplit(sep, 1)[-1]
    return s


@dataclass(frozen=True)
class RelSpec:
    src_cls: URIRef
    pred: URIRef
    rel_type: str
    # target can be any node type in our model; we do not enforce dst class here


REL_SPECS: list[RelSpec] = [
    RelSpec(CLS_RSD, P_HAS_KEYWORD,    "HAS_KEYWORD"),
    RelSpec(CLS_RSD, P_HAS_CATEGORY,   "HAS_CATEGORY"),
    RelSpec(CLS_RSD, P_HAS_STANDARD,   "HAS_STANDARD"),
    RelSpec(CLS_RSD, P_HAS_OCCUPATION, "HAS_OCCUPATION"),
    RelSpec(CLS_RSD, P_IN_COLLECTION,  "IN_COLLECTION"),
    RelSpec(CLS_RSD, P_HAS_ALIGNMENT,  "HAS_ALIGNMENT"),
    # occupation hierarchy
    RelSpec(CLS_OCCUPATION, P_PART_OF, "PART_OF"),
]

__all__ = [
    # namespaces
    "BASE", "RDF", "RDFS", "SKOS", "DCTERMS", "XSD",
    # classes
    "CLS_RSD", "CLS_KEYWORD", "CLS_CATEGORY", "CLS_STANDARD",
    "CLS_OCCUPATION", "CLS_COLLECTION", "CLS_ALIGNMENT",
    # properties
    "P_HAS_KEYWORD", "P_HAS_CATEGORY", "P_HAS_STANDARD",
    "P_HAS_OCCUPATION", "P_IN_COLLECTION", "P_HAS_ALIGNMENT", "P_PART_OF",
    "P_PREF_LABEL", "P_ALT_LABEL", "P_NOTATION", "P_STATUS", "P_IDENTIFIER",
    "P_TITLE", "P_SOURCE", "P_CREATED", "P_ISSUED", "P_MODIFIED", "P_DEFINITION",
    # headers
    "HDR_RSD", "HDR_KEYWORD", "HDR_CATEGORY", "HDR_STANDARD",
    "HDR_OCCUPATION", "HDR_COLLECTION", "HDR_ALIGNMENT", "HDR_REL",
    # helpers
    "localname", "RelSpec", "REL_SPECS",
]
