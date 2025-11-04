#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON → TTL, single-file.
- take ONE OSMT JSON file (RichSkillDescriptor)
- emit ONE TTL file
"""

import json
import re
from pathlib import Path
from urllib.parse import urlparse
from logging import Logger

from rdflib.namespace import XSD  # noqa: F401  kept for future typed literals
from wgu_osmt_builder.common.log import configure_logger


class TransformJSONtoTTL:
    BASE_IRI = "https://w3id.org/wgu/osmt/skills#"

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger or configure_logger(__name__)
        self._slug_re = re.compile(r"[^a-z0-9]+", re.IGNORECASE)

    def process(self, src_json_path: str, dst_ttl_path: str) -> None:
        src = Path(src_json_path)
        dst = Path(dst_ttl_path)

        data = self._load_json(src)
        ttl_str = self._build_ttl(data)

        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(ttl_str, encoding="utf-8")

        self.logger.info(json.dumps({
            "json2ttl": "ok",
            "src": str(src),
            "dst": str(dst),
        }))

    # ---------- IO ----------
    def _load_json(self, path: Path) -> dict[str, object]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # ---------- slug / literal ----------
    def _slug(self, label: str) -> str:
        if not label:
            return ""
        s = label.strip().lower().replace("&", "and")
        s = self._slug_re.sub("-", s)
        s = re.sub(r"-{2,}", "-", s).strip("-")
        return s

    def _lit(self, s: str) -> str:
        if s is None:
            return ""
        s = str(s)
        s = s.replace("\\", "\\\\")
        s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        s = s.strip().replace('"', '\\"')
        return s

    # ---------- IRI factories ----------
    def _iri_for_rsd(self, uuid_str: str) -> str:
        return f":rsd-{uuid_str}"

    def _iri_for_keyword(self, label: str) -> str:
        return f":kw-{self._slug(label) or 'unnamed'}"

    def _iri_for_category(self, label: str) -> str:
        return f":cat-{self._slug(label) or 'unnamed'}"

    def _iri_for_collection(self, uuid_str: str) -> str:
        return f":col-{uuid_str}"

    def _iri_for_alignment(self, alignment_id: str) -> str:
        parsed = urlparse(alignment_id)
        if parsed.scheme and parsed.path:
            last = parsed.path.rstrip("/").split("/")[-1]
            slug = self._slug(last)
        else:
            slug = self._slug(alignment_id)
        return f":align-{slug or 'alignment'}"

    def _iri_for_standard(self, code: str) -> str:
        return f":std-{self._slug(code) or 'std'}"

    def _iri_for_occupation(self, code: str) -> str:
        return f":bls-{code}"

    # ---------- TTL builders ----------
    def _ttl_header(self) -> str:
        return """@prefix :      <https://w3id.org/wgu/osmt/skills#> .
@base          <https://w3id.org/wgu/osmt/skills#> .

@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix dct:   <http://purl.org/dc/terms/> .

<https://w3id.org/wgu/osmt/skills> rdf:type owl:Ontology .

#################################################################
#    Structural classes
#################################################################

:RichSkillDescriptor rdf:type owl:Class .
:Keyword             rdf:type owl:Class .
:Category            rdf:type owl:Class .
:Standard            rdf:type owl:Class .
:Occupation          rdf:type owl:Class .
:Collection          rdf:type owl:Class .
:Alignment           rdf:type owl:Class .

#################################################################
#    Structural properties
#################################################################

:hasKeyword    rdf:type owl:ObjectProperty .
:hasCategory   rdf:type owl:ObjectProperty .
:hasStandard   rdf:type owl:ObjectProperty .
:hasOccupation rdf:type owl:ObjectProperty .
:inCollection  rdf:type owl:ObjectProperty .
:hasAlignment  rdf:type owl:ObjectProperty .
:partOf        rdf:type owl:ObjectProperty .

"""

    def _build_ttl(self, data: dict[str, object]) -> str:
        keywords = data.get("keywords") or []
        category = data.get("category")
        standards = data.get("standards") or []
        collections = data.get("collections") or []
        alignments = data.get("alignments") or []
        occupations = data.get("occupations") or []

        parts: list[str] = []
        parts.append(self._ttl_header())

        parts += [
            "#################################################################",
            "#    RSD",
            "#################################################################\n",
            self._build_rsd_block(data),
            "\n#################################################################",
            "#    Keywords",
            "#################################################################\n",
            self._build_keywords_block([str(k) for k in keywords]),
            "\n#################################################################",
            "#    Category",
            "#################################################################\n",
            self._build_category_block(str(category) if category else None),
            "\n#################################################################",
            "#    Standards",
            "#################################################################\n",
            self._build_standards_block(standards),
            "\n#################################################################",
            "#    Collections",
            "#################################################################\n",
            self._build_collections_block(collections),
            "\n#################################################################",
            "#    Alignments",
            "#################################################################\n",
            self._build_alignments_block(alignments),
            "\n#################################################################",
            "#    Occupations",
            "#################################################################\n",
            self._build_occupations_block(occupations),
        ]

        return "\n".join(parts)

    # ---------- blocks ----------
    def _build_rsd_block(self, data: dict[str, object]) -> str:
        uuid_str = data.get("uuid") or data.get("id")
        if isinstance(uuid_str, str) and uuid_str.startswith("https://"):
            uuid_str = uuid_str.rsplit("/", 1)[-1]
        uuid_str = str(uuid_str)

        rsd_iri = self._iri_for_rsd(uuid_str)

        skill_name = self._lit(data.get("skillName", ""))
        skill_stmt = self._lit(data.get("skillStatement", ""))
        creator = data.get("creator")
        author = data.get("author")
        category = data.get("category")
        status = self._lit(data.get("status", ""))

        publish_date = data.get("publishDate")
        creation_date = data.get("creationDate")
        update_date = data.get("updateDate")

        src_id = data.get("id")

        lines: list[str] = []
        lines.append(f"{rsd_iri}")
        lines.append("    rdf:type        :RichSkillDescriptor ;")
        if skill_name:
            lines.append(f'    dct:title       "{skill_name}" ;')
            lines.append(f'    skos:prefLabel  "{skill_name}"@en ;')
        lines.append(f'    dct:identifier  "{uuid_str}" ;')
        if isinstance(src_id, str):
            lines.append(f"    dct:source      <{src_id}> ;")
        if creator:
            lines.append(f"    dct:creator     <{creator}> ;")
        elif author:
            lines.append(f'    dct:creator     "{self._lit(author)}" ;')
        if creation_date:
            lines.append(
                f'    dct:created     "{creation_date}"^^xsd:dateTime ;')
        if publish_date:
            lines.append(
                f'    dct:issued      "{publish_date}"^^xsd:dateTime ;')
        if update_date:
            lines.append(
                f'    dct:modified    "{update_date}"^^xsd:dateTime ;')
        if status:
            lines.append(f'    :status         "{status}" ;')
        if skill_stmt:
            lines.append(f'    skos:definition "{skill_stmt}"@en ;')

        if category:
            cat_iri = self._iri_for_category(str(category))
            lines.append(f"    :hasCategory    {cat_iri} ;")

        kws = data.get("keywords") or []
        kw_iris = [self._iri_for_keyword(str(kw)) for kw in kws if str(kw)]
        if kw_iris:
            lines.append(f"    :hasKeyword     { ' , '.join(kw_iris) } ;")

        stds = data.get("standards") or []
        std_iris: list[str] = []
        for std in stds:
            code = str(std.get("skillName", "")).strip() if isinstance(
                std, dict) else str(std).strip()
            if code:
                std_iris.append(self._iri_for_standard(code))
        if std_iris:
            lines.append(f"    :hasStandard    { ' , '.join(std_iris) } ;")

        occs = data.get("occupations") or []
        occ_iris: list[str] = []
        for occ in occs:
            code = str(occ.get("code", "")).strip()
            if code:
                occ_iris.append(self._iri_for_occupation(code))
        if occ_iris:
            lines.append(f"    :hasOccupation  { ' , '.join(occ_iris) } ;")

        cols = data.get("collections") or []
        col_iris: list[str] = []
        for c in cols:
            cuuid = str(c.get("uuid", "")).strip()
            if cuuid:
                col_iris.append(self._iri_for_collection(cuuid))
        if col_iris:
            lines.append(f"    :inCollection   { ' , '.join(col_iris) } ;")

        aligns = data.get("alignments") or []
        align_iris: list[str] = []
        for a in aligns:
            aid = a.get("id") or a.get("skillName")
            if aid:
                align_iris.append(self._iri_for_alignment(str(aid)))
        if align_iris:
            lines.append(f"    :hasAlignment   { ' , '.join(align_iris) } ;")

        lines[-1] = lines[-1].rstrip(" ;") + " ."
        return "\n".join(lines)

    def _build_keywords_block(self, keywords: list[str]) -> str:
        parts: list[str] = []
        for kw in keywords:
            if not kw:
                continue
            iri = self._iri_for_keyword(str(kw))
            label = self._lit(str(kw).replace("_", " "))
            parts.append(
                f"{iri}\n"
                f"    rdf:type       :Keyword ;\n"
                f"    skos:prefLabel \"{label}\"@en .\n"
            )
        return "\n".join(parts)

    def _build_category_block(self, category: str | None) -> str:
        if not category:
            return ""
        iri = self._iri_for_category(category)
        label = self._lit(category.replace("_", " "))
        return (
            f"{iri}\n"
            f"    rdf:type       :Category ;\n"
            f"    skos:prefLabel \"{label}\"@en .\n"
        )

    def _build_standards_block(self, stds: list[object]) -> str:
        parts: list[str] = []
        for std in stds:
            code = str(std.get("skillName", "")).strip() if isinstance(
                std, dict) else str(std).strip()
            if not code:
                continue
            code_lit = self._lit(code)
            iri = self._iri_for_standard(code)
            parts.append(
                f"{iri}\n"
                f"    rdf:type        :Standard ;\n"
                f"    skos:prefLabel  \"{code_lit}\"@en ;\n"
                f"    skos:notation   \"{code_lit}\" ;\n"
                f"    dct:source      <https://niccs.cisa.gov/workforce-development/nice-framework> .\n"
            )
        return "\n".join(parts)

    def _build_collections_block(self, cols: list[dict[str, object]]) -> str:
        parts: list[str] = []
        for c in cols:
            cuuid = str(c.get("uuid", "")).strip()
            name = self._lit(str(c.get("name", "")).strip())
            if not cuuid:
                continue
            iri = self._iri_for_collection(cuuid)
            parts.append(
                f"{iri}\n"
                f"    rdf:type       :Collection ;\n"
                f"    dct:identifier \"{cuuid}\" ;\n"
                f"    dct:title      \"{name}\" .\n"
            )
        return "\n".join(parts)

    def _build_alignments_block(self, aligns: list[dict[str, object]]) -> str:
        parts: list[str] = []
        for a in aligns:
            aid_raw = a.get("id") or a.get("skillName")
            if not aid_raw:
                continue
            aid = str(aid_raw)
            iri = self._iri_for_alignment(aid)
            name = self._lit(str(a.get("skillName", aid)).strip())
            parts.append(
                f"{iri}\n"
                f"    rdf:type       :Alignment ;\n"
                f"    dct:identifier \"{self._lit(aid)}\" ;\n"
                f"    skos:prefLabel \"{name}\"@en .\n"
            )
        return "\n".join(parts)

    def _build_occupations_block(self, occs: list[dict[str, object]]) -> str:
        parts: list[str] = []
        for occ in occs:
            code = str(occ.get("code", "")).strip()
            name = self._lit(str(occ.get("targetNodeName", "")).strip())
            if not code:
                continue
            iri = self._iri_for_occupation(code)
            parents = occ.get("parents") or []
            parent_links: list[str] = []
            for p in parents:
                pcode = str(p.get("code", "")).strip()
                if pcode and pcode != code:
                    parent_links.append(self._iri_for_occupation(pcode))
            line = (
                f"{iri}\n"
                f"    rdf:type       :Occupation ;\n"
                f"    dct:identifier \"{code}\" ;\n"
                f"    skos:prefLabel \"{name}\"@en"
            )
            if parent_links:
                line += f" ;\n    :partOf        { ' , '.join(parent_links) } .\n"
            else:
                line += " .\n"
            parts.append(line)
        return "\n".join(parts)
