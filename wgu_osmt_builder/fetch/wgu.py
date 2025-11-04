#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Fetch WGU OSMT Skills (JSON-only)

- read a CSV of skills
- keep only rows whose Canonical URL starts with https://osmt.wgu.edu
- for each URL, download JSON once and save as <skill-id>.json
- skip if file already exists
"""

import os
import csv
import json
import time
import random
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from wgu_osmt_builder.common.log import configure_logger
from wgu_osmt_builder.common.ua import user_agents
from wgu_osmt_builder.common.config import PROXIES_PATH

_OSMT_HOST = "https://osmt.wgu.edu"

logger = configure_logger(__name__)


def _build_session() -> requests.Session:
    """Session with retries. No globals."""
    s = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        backoff_factor=0.5,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry, pool_connections=16, pool_maxsize=32)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


class FetchWGUData:
    def __init__(
        self,
        csv_path: str,
        output_root: str | None = None,
        proxies_path: str | None = None,
        pause_seconds: float = 0.5,
        session: requests.Session | None = None,
    ):
        self.csv_path = Path(csv_path)
        self.output_root = (
            Path(output_root)
            if output_root
            else Path(os.getcwd()) / "resources" / "output" / "wgu-skills"
        )
        self.output_root.mkdir(parents=True, exist_ok=True)

        self.pause_seconds = pause_seconds
        self.session = session or _build_session()

        proxy_file = Path(proxies_path) if proxies_path else PROXIES_PATH
        self.proxies = self._load_proxies(proxy_file)
        self.proxy_health: dict[str, bool] = {}

        try:
            self.real_ip = self.session.get(
                "https://httpbin.org/ip", timeout=10).json().get("origin")
            logger.info(f"🌎 Real outgoing IP: {self.real_ip}")
        except Exception as ex:
            self.real_ip = None
            logger.warning(f"⚠️ Could not determine real IP: {ex}")

    # ------------------------
    # Proxies
    # ------------------------
    def _load_proxies(self, path: Path) -> list[str]:
        if not path.exists():
            logger.info(
                f"ℹ️ No proxies file at {path}. Using direct requests.")
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        proxies: list[str] = []
        for line in lines:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            proxies.append(s)
        logger.info(f"🌍 Loaded {len(proxies)} proxies")
        return proxies

    def _verify_proxy_once(self, proxy: str) -> bool:
        if proxy in self.proxy_health:
            return self.proxy_health[proxy]

        logger.info(f"🧪 Verifying proxy {proxy} ...")
        proxy_url = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            r = self.session.get("https://httpbin.org/ip",
                                 proxies=proxy_url, timeout=10)
            if r.status_code != 200:
                logger.warning(
                    f"⚠️ Proxy {proxy} returned HTTP {r.status_code}")
                self.proxy_health[proxy] = False
                return False

            reported_ip = r.json().get("origin")
            if reported_ip and (self.real_ip is None or reported_ip != self.real_ip):
                logger.info(f"✅ Proxy {proxy} OK ({reported_ip})")
                self.proxy_health[proxy] = True
            else:
                logger.warning(
                    f"❌ Proxy {proxy} leaks or equals real IP ({reported_ip})")
                self.proxy_health[proxy] = False
        except Exception as ex:
            logger.warning(f"💀 Proxy {proxy} failed: {ex}")
            self.proxy_health[proxy] = False

        time.sleep(0.25)
        return self.proxy_health[proxy]

    def _random_proxy(self) -> dict | None:
        if not self.proxies:
            return None
        for _ in range(len(self.proxies)):
            proxy = random.choice(self.proxies)
            if self._verify_proxy_once(proxy):
                return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        logger.warning("⚠️ No healthy proxy available.")
        return None

    def _random_user_agent(self) -> str:
        return random.choice(user_agents)

    # ------------------------
    # CSV
    # ------------------------
    def _read_skill_urls(self) -> list[str]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        urls: list[str] = []
        with self.csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = (row.get("Canonical URL") or "").strip()
                if url and url.startswith(_OSMT_HOST):
                    urls.append(url)
        logger.info(f"📄 CSV provided {len(urls)} WGU skill URLs")
        return urls

    # ------------------------
    # Paths
    # ------------------------
    def _skill_id_from_url(self, url: str) -> str:
        return url.rstrip("/").split("/")[-1]

    def _outfile(self, skill_id: str) -> Path:
        return self.output_root / f"{skill_id}.json"

    def _exists(self, skill_id: str) -> bool:
        return self._outfile(skill_id).exists()

    # ------------------------
    # HTTP (JSON-only)
    # ------------------------
    def _fetch_json(self, url: str, skill_id: str) -> dict | None:
        proxy = self._random_proxy()
        ua = self._random_user_agent()
        headers = {
            "Accept": "application/json,text/plain;q=0.9,*/*;q=0.8",
            "User-Agent": ua,
        }

        label = proxy["http"].split("//")[1] if proxy else "direct"
        logger.info(f"🌐 GET {url} via {label}")

        try:
            r = self.session.get(url, headers=headers,
                                 proxies=proxy, timeout=(10, 60))
        except requests.exceptions.RequestException as ex:
            logger.warning(f"💥 Request failed for {url}: {ex}")
            return None

        if r.status_code != 200:
            logger.warning(f"⚠️ HTTP {r.status_code} for {url}")
            return None

        ct = r.headers.get("Content-Type", "")
        if "application/json" not in ct:
            logger.info(
                f"ℹ️ Non-JSON Content-Type for {url}: '{ct}'. Attempting JSON decode anyway.")

        try:
            return r.json()
        except Exception as ex:
            logger.warning(f"⚠️ JSON decode error for {url}: {ex}")
            return None

    # ------------------------
    # Save
    # ------------------------
    def _save_json(self, skill_id: str, data: dict) -> None:
        out = self._outfile(skill_id)
        out.write_text(json.dumps(data, ensure_ascii=False,
                       indent=4), encoding="utf-8")
        logger.info(f"📦 Saved {skill_id}.json")

    # ------------------------
    # Runner
    # ------------------------
    def process(self) -> None:
        urls = self._read_skill_urls()
        if not urls:
            logger.info("⚠️ No WGU URLs to process.")
            return

        random.shuffle(urls)

        for url in urls:
            skill_id = self._skill_id_from_url(url)
            if self._exists(skill_id):
                logger.info(f"🔁 Skip {skill_id}.json (already exists)")
                continue

            data = self._fetch_json(url, skill_id)
            if data:
                self._save_json(skill_id, data)
            else:
                logger.warning(f"🚫 No data for {url}")

            time.sleep(self.pause_seconds)
