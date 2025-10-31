# WGU OSMT Fetcher

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Source](https://img.shields.io/badge/source-WGU%20OSMT-orange.svg)
![HTTP](https://img.shields.io/badge/http-requests-success.svg)
![Proxies](https://img.shields.io/badge/proxy-optional-lightgrey.svg)

## Purpose

Download public WGU OSMT skill JSON from CSV files that list their canonical URLs.

Flow:

1. Orchestrator walks a directory and finds CSVs.
2. Keeps only CSVs that have a `Canonical URL` column.
3. For each CSV calls the fetch service.
4. Service downloads every `https://osmt.wgu.edu/...` URL, once.
5. Saves as `<uuid>.json` under `resources/output/wgu-skills/`.
6. Skips files that already exist.

## Repo layout

```
wgu-osmt/
├── Makefile
├── pyproject.toml
├── resources/
│ └── input/
│ └── proxies.txt # optional
└── wgu_osmt/
├── orchestrator.py
└── svc/
└── fetch_wgu_data.py
```

- `wgu_osmt/orchestrator.py` = entry point.
- `wgu_osmt/svc/fetch_wgu_data.py` = per-CSV downloader.
- `resources/input/proxies.txt` = optional list of proxies.

## What the orchestrator does

- Recurses under a root directory (default `resources/input`).
- Finds every `*.csv`.
- Opens the file and checks the header.
- If header contains `Canonical URL` it processes it.
- Otherwise it logs and skips.

This matches your code:

```
python -m wgu_osmt.orchestrator resources/input
```

or

```
python wgu_osmt/orchestrator.py resources/input
```

If no arg is given it uses the env var:

- `WGU_CSV_ROOT=...`

or falls back to:

- `resources/input`

## CSV requirements

The CSV must have:

- a header row
- a column named `Canonical URL`

Example:

```
"Canonical URL","RSD Name","Skill Statement",...
"https://osmt.wgu.edu/api/skills/de1ed4d0-78ce-4072-917b-1d35c41e37e0","New Technology Implementation",...
```

The service will ignore every URL that does **not** start with:

- `https://osmt.wgu.edu`

So if the CSV also has `https://skills.emsidata.com/...` those will be skipped.

## Download rules

Given a URL:

- `https://osmt.wgu.edu/api/skills/de1ed4d0-78ce-4072-917b-1d35c41e37e0`

we extract the last segment:

- `de1ed4d0-78ce-4072-917b-1d35c41e37e0`

and save to:

- `resources/output/wgu-skills/de1ed4d0-78ce-4072-917b-1d35c41e37e0.json`

If that file exists we do **not** call the URL again.

## Service (fetch_wgu_data.py)

The service:

1. Reads the CSV.
2. Filters to URLs that start with `https://osmt.wgu.edu`.
3. For each URL
   - derive `skill_id`
   - check if file exists
   - if not, GET JSON
   - save compact JSON

JSON is saved without indent to keep files small.

## Proxies

The service looks for:

- `resources/input/proxies.txt`

Format:

```
1.2.3.4:8080
5.6.7.8:3128
```

If the file is present it will:

- load all proxies
- verify each proxy once via `https://httpbin.org/ip`
- mark bad or leaky proxies
- choose a healthy proxy for each request

If the file is **not** present it logs:

- `No proxies file ... Using direct requests.`

and just uses direct HTTP.

## Logging

Both orchestrator and service use:

- `wgu_osmt.dto.configure_logger`

Typical messages:

- `📂 Found N CSV file(s) under ...`
- `⏭️ Skip non-WGU CSV: ...`
- `▶️ Processing WGU CSV: ...`
- `🌐 GET https://osmt.wgu.edu/... via direct`
- `📦 Saved <uuid>.json`
- `🔁 Skip <uuid>.json (already exists)`

This makes runs idempotent and traceable.

## Running examples

Run orchestrator on default location:

```
python -m wgu_osmt.orchestrator
```

Run orchestrator on a specific folder:

```
python -m wgu_osmt.orchestrator /tmp/wgu-csvs
```

Run service directly on one CSV:

```
python -c "from wgu_osmt.svc.fetch_wgu_data import FetchWGUData; FetchWGUData(csv_path='resources/input/wgu-skills.csv').process()"
```

## Notes

- No HTML/DOM scraping. Endpoint is already JSON.
- Only `https://osmt.wgu.edu...` is pulled.
- Safe to re-run. Existing JSON is skipped.
- If WGU changes the column name from `Canonical URL` then the orchestrator will skip that CSV; update `is_wgu_csv` if that happens.
