# WGU OSMT Builder

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![RDF/Turtle](https://img.shields.io/badge/RDF-Turtle-0a7bbc.svg)](#)
[![rdflib 6.x](https://img.shields.io/badge/rdflib-6.x-green.svg)](#)
[![CLI](https://img.shields.io/badge/CLI-wgu__osmt__builder-lightgrey.svg)](#)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)](#)
[![Ontology TTL](https://img.shields.io/badge/TTL-wgu--osmt--skills--ontology-blueviolet.svg)](https://github.com/craigtrim/wgu-osmt-skills-ontology/releases)
[![Dataset](https://img.shields.io/badge/dataset-wgu--osmt--skills--dataset-orange.svg)](https://github.com/craigtrim/wgu-osmt-skills-dataset)

Convert WGU OSMT skill JSON to Turtle and generate label reports. Optionally fetch JSON from WGU export CSVs.

## Artifacts

- Canonical TTL releases: **wgu-osmt-skills-ontology**  
  https://github.com/craigtrim/wgu-osmt-skills-ontology
- Canonical JSON skills + CSV collections: **wgu-osmt-skills-dataset**  
  https://github.com/craigtrim/wgu-osmt-skills-dataset

## Layout

```
wgu_osmt_builder/
  common/        # logging, paths, CLI, proxies config
  fetch/         # collections orchestrator, JSON fetcher
  build/         # JSON→TTL converter, assembler
  validate/      # report extractors
  data/
    sources/     # CSV collections (inputs)
    raw/         # downloaded JSON skills (inputs)
    out/
      ttl/       # per-skill TTL + merged skills.ttl
      reports/   # extracted label lists
```

Paths are centralized in `wgu_osmt_builder/common/paths.py`: `DATA`, `SOURCES`, `RAW`, `OUT`, `TTL_OUT`, `REPORTS`.

## Quickstart

Install
```
poetry install
```

Fetch JSON from CSVs in `data/sources`
```
poetry run python -m wgu_osmt_builder.common.cli fetch --dir wgu_osmt_builder/data/sources
```

Build TTL and merge to `data/out/ttl/skills.ttl`
```
poetry run python -m wgu_osmt_builder.common.cli build
```

Generate reports to `data/out/reports/`
```
poetry run python -m wgu_osmt_builder.common.cli validate
```

## CLI

Fetch from a directory of CSVs (CSV must contain **Canonical URL**)
```
python -m wgu_osmt_builder.common.cli fetch --dir <dir>
```

Fetch from a single CSV
```
python -m wgu_osmt_builder.common.cli fetch --csv <file> [--out <json_out>] [--proxies <proxies.txt>] [--pause 0.5]
```

Build JSON → TTL and merge
```
python -m wgu_osmt_builder.common.cli build [--json-root <dir>] [--ttl-out <dir>] [--merged <path>]
```

Validate reports from `skills.ttl`
```
python -m wgu_osmt_builder.common.cli validate [--ttl <path>] [--out-dir <dir>] [--lang en] [--alt] [--alignments|--bls|--keywords|--rsd|--all]
```

## Make targets

```
make fetch       # fetch JSON from data/sources
make build_ttl   # build per-skill TTL and merged skills.ttl
make validate    # generate label reports
```

## Proxies (optional)

Place `proxies.txt` in `wgu_osmt_builder/common/config/`:
```
1.2.3.4:8080
5.6.7.8:3128
```
If absent the fetcher uses direct requests.
