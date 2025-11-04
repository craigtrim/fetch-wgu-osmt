# wgu_osmt_builder/paths.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
CACHE = DATA / "cache"
OUT = DATA / "out"
TTL_OUT = OUT / "ttl"
REPORTS = OUT / "reports"
SOURCES = DATA / "sources"
GRAPH = OUT / "graph"
