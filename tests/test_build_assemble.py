#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
from pathlib import Path

import pytest
from rdflib import Graph

from wgu_osmt_builder.build.assemble import process_directory
from wgu_osmt_builder.build.json2ttl import TransformJSONtoTTL


def _rsd(uuid: str, name: str) -> dict:
    return {
        "type": "RichSkillDescriptor",
        "uuid": uuid,
        "id": f"https://osmt.wgu.edu/skills/{uuid}",
        "skillName": name,
        "skillStatement": f"{name} statement",
        "keywords": ["alpha", "beta"],
        "category": "demo_category",
        "standards": ["NICE-ABC-123"],
        "collections": [{"uuid": "11111111-1111-1111-1111-111111111111", "name": "Demo Collection"}],
        "alignments": [{"id": "https://example.org/align/foo", "skillName": "Foo Align"}],
        "occupations": [{"code": "15-1252", "targetNodeName": "Software Developers"}],
    }


@pytest.mark.parametrize("count", [2])
def test_assemble_json_to_ttl_and_merge(tmp_path: Path, count: int) -> None:
    # Arrange: temp dirs
    json_root = tmp_path / "input_json"
    ttl_out = tmp_path / "out_ttl"
    merged_path = ttl_out / "skills.ttl"  # required output name
    json_root.mkdir(parents=True, exist_ok=True)

    # Write minimal valid RSD JSON files
    uuids = [f"00000000-0000-0000-0000-00000000000{i}" for i in range(count)]
    for u in uuids:
        (json_root / f"{u}.json").write_text(json.dumps(_rsd(u, f"Skill {u[-1]}")), encoding="utf-8")

    # Act
    process_directory(json_root, ttl_out, merged_path)

    # Assert: per-file TTLs exist
    for u in uuids:
        ttl_file = ttl_out / f"{u}.ttl"
        assert ttl_file.exists(), f"Missing TTL for {u}"
        txt = ttl_file.read_text(encoding="utf-8")
        # Namespace check in each file header
        assert "https://w3id.org/wgu/osmt/skills" in txt, "Wrong or missing namespace in TTL header"
        # RSD subject present
        assert f":rsd-{u}" in txt

    # Assert: merged file exists and parses
    assert merged_path.exists(), "Merged skills.ttl not created"
    g = Graph()
    g.parse(location=str(merged_path), format="turtle")
    # Sanity: at least one triple for first RSD label
    q = """
    PREFIX : <https://w3id.org/wgu/osmt/skills#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?o WHERE { :rsd-00000000-0000-0000-0000-000000000000 skos:prefLabel ?o }
    """
    res = list(g.query(q))
    assert res and str(res[0][0]).startswith("Skill"), "Merged graph missing expected RSD label"
