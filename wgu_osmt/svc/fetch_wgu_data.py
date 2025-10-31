#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Fetch WGU OSMT Skills

- read a CSV of skills
- keep only rows whose Canonical URL starts with https://osmt.wgu.edu
- for each URL, download JSON once and save as <skill-id>.json
- skip if file already exists
- optional rotating proxies + user-agents (same pattern as your OpenSyllabus fetcher)
"""

import os
import csv
import json
import time
import random
import requests
from typing import Optional

from wgu_osmt.dto import configure_logger, user_agents


class FetchWGUData:
    def __init__(
        self,
        csv_path: str,
        output_root: str | None = None,
        proxies_path: str = "resources/config/proxies.txt",
        pause_seconds: float = 0.5,
    ):
        self.logger = configure_logger(__name__)

        self.csv_path = csv_path
        self.output_root = (
            output_root
            if output_root
            else os.path.join(os.getcwd(), "resources", "output", "wgu-skills")
        )
        os.makedirs(self.output_root, exist_ok=True)

        self.pause_seconds = pause_seconds

        # optional proxies (same pattern as your OS fetcher)
        self.proxies = self._load_proxies(proxies_path)
        self.proxy_health: dict[str, bool] = {}

        # try to learn real IP once, for leak detection
        try:
            self.real_ip = requests.get(
                "https://httpbin.org/ip", timeout=10).json().get("origin")
            self.logger.info(f"🌎 Real outgoing IP: {self.real_ip}")
        except Exception as ex:
            self.real_ip = None
            self.logger.warning(f"⚠️ Could not determine real IP: {ex}")

    # ------------------------------------------------------------------
    # Proxies
    # ------------------------------------------------------------------
    def _load_proxies(self, path: str) -> list[str]:
        if not os.path.exists(path):
            self.logger.info(
                f"ℹ️ No proxies file at {path}. Using direct requests.")
            return []
        with open(path, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
        self.logger.info(f"🌍 Loaded {len(proxies)} proxies")
        return proxies

    def _verify_proxy_once(self, proxy: str) -> bool:
        if proxy in self.proxy_health:
            return self.proxy_health[proxy]

        self.logger.info(f"🧪 Verifying proxy {proxy} ...")
        proxy_url = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            r = requests.get("https://httpbin.org/ip",
                             proxies=proxy_url, timeout=10)
            if r.status_code != 200:
                self.logger.warning(
                    f"⚠️ Proxy {proxy} returned HTTP {r.status_code}")
                self.proxy_health[proxy] = False
                return False

            reported_ip = r.json().get("origin")
            if reported_ip and (self.real_ip is None or reported_ip != self.real_ip):
                self.logger.info(f"✅ Proxy {proxy} OK ({reported_ip})")
                self.proxy_health[proxy] = True
            else:
                self.logger.warning(
                    f"❌ Proxy {proxy} leaks or equals real IP ({reported_ip})")
                self.proxy_health[proxy] = False
        except Exception as ex:
            self.logger.warning(f"💀 Proxy {proxy} failed: {ex}")
            self.proxy_health[proxy] = False

        time.sleep(0.25)
        return self.proxy_health[proxy]

    def _random_proxy(self) -> Optional[dict]:
        if not self.proxies:
            return None
        # iterate at most N times to find a good one
        for _ in range(len(self.proxies)):
            proxy = random.choice(self.proxies)
            if self._verify_proxy_once(proxy):
                return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.logger.warning("⚠️ No healthy proxy available.")
        return None

    def _random_user_agent(self) -> str:
        return random.choice(user_agents)

    # ------------------------------------------------------------------
    # CSV
    # ------------------------------------------------------------------
    def _read_skill_urls(self) -> list[str]:
        """Return only osmt.wgu.edu URLs from the CSV."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")

        urls: list[str] = []
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = (row.get("Canonical URL") or "").strip()
                if not url:
                    continue
                # only what you asked for
                if url.startswith("https://osmt.wgu.edu"):
                    urls.append(url)
        self.logger.info(f"📄 CSV provided {len(urls)} WGU skill URLs")
        return urls

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    def _skill_id_from_url(self, url: str) -> str:
        # e.g. https://osmt.wgu.edu/api/skills/de1ed4d0-... -> de1ed4d0-...
        return url.rstrip("/").split("/")[-1]

    def _outfile(self, skill_id: str) -> str:
        return os.path.join(self.output_root, f"{skill_id}.json")

    def _exists(self, skill_id: str) -> bool:
        return os.path.exists(self._outfile(skill_id))

    def _fetch_json(self, url: str) -> dict | None:
        proxy = self._random_proxy()
        ua = self._random_user_agent()
        headers = {
            "Accept": "application/json",
            "User-Agent": ua,
        }

        label = proxy["http"].split("//")[1] if proxy else "direct"
        self.logger.info(f"🌐 GET {url} via {label}")

        try:
            r = requests.get(url, headers=headers,
                             proxies=proxy, timeout=(10, 60))
        except requests.exceptions.RequestException as ex:
            self.logger.warning(f"💥 Request failed for {url}: {ex}")
            return None

        if r.status_code != 200:
            self.logger.warning(f"⚠️ HTTP {r.status_code} for {url}")
            return None

        text = r.text.strip()
        if not text:
            self.logger.warning(f"⚠️ Empty body for {url}")
            return None

        try:
            return r.json()
        except Exception as ex:
            self.logger.warning(f"⚠️ JSON decode error for {url}: {ex}")
            return None

    def _save_json(self, skill_id: str, data: dict):
        path = self._outfile(skill_id)
        # compact JSON, no indent, to keep it small
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self.logger.info(f"📦 Saved {skill_id}.json")

    # ------------------------------------------------------------------
    # Runner
    # ------------------------------------------------------------------
    def process(self):
        urls = self._read_skill_urls()
        if not urls:
            self.logger.info("⚠️ No WGU URLs to process.")
            return

        for url in urls:
            skill_id = self._skill_id_from_url(url)
            if self._exists(skill_id):
                self.logger.info(f"🔁 Skip {skill_id}.json (already exists)")
                continue

            data = self._fetch_json(url)
            if data:
                self._save_json(skill_id, data)
            else:
                self.logger.warning(f"🚫 No data for {url}")

            time.sleep(self.pause_seconds)
