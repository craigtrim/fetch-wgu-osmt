#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import subprocess

from tabulate import tabulate

URI  = os.environ["wgu_osmt_skills_builder_uri"]
USER = os.environ["wgu_osmt_skills_builder_user"]
DB   = os.environ["wgu_osmt_skills_builder_db"]
PW   = os.environ["NEO_PW"]  # provided by neo_load.sh

Q_SUMMARY = """
MATCH (n) RETURN 'nodes' AS item, count(n) AS count
UNION ALL
MATCH ()-[r]->() RETURN 'relationships' AS item, count(r) AS count
"""

# No variable shadowing. Simple aggregates.
Q_NODES = """
MATCH (n)
UNWIND labels(n) AS label
RETURN label, count(*) AS count
ORDER BY label
"""

Q_RELS = """
MATCH ()-[r]->()
RETURN type(r) AS type, count(*) AS count
ORDER BY type
"""

def run_cypher(cypher: str) -> str:
    cmd = [
        "cypher-shell",
        "-a", URI,
        "-u", USER,
        "-p", PW,
        "-d", DB,
        "--format", "plain",
        "--wrap", "false",
        "--fail-fast",
        "--non-interactive",
    ]
    proc = subprocess.run(cmd, input=cypher, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cypher-shell failed: {proc.stderr.strip()}")
    return proc.stdout.strip()

def parse_plain_pairs(text: str) -> list[tuple[str, str]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    # drop header line if present
    if "," in lines[0] and not lines[0].startswith('"'):
        lines = lines[1:]
    out: list[tuple[str, str]] = []
    for ln in lines:
        if "," not in ln:
            continue
        k, v = ln.split(",", 1)
        out.append((k.strip().strip('"'), v.strip()))
    return out

def main() -> None:
    summary = parse_plain_pairs(run_cypher(Q_SUMMARY))
    nodes   = parse_plain_pairs(run_cypher(Q_NODES))
    rels    = parse_plain_pairs(run_cypher(Q_RELS))

    print("\n📊 Summary")
    print(tabulate(summary, headers=["item", "count"], tablefmt="github"))

    print("\n🧱 Nodes by label")
    print(tabulate(nodes, headers=["label", "count"], tablefmt="github"))

    print("\n🔗 Relationships by type")
    print(tabulate(rels, headers=["type", "count"], tablefmt="github"))

if __name__ == "__main__":
    main()
