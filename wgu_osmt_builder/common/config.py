from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "wgu_osmt_builder" / "common" / "config"

# Allow override
PROXIES_PATH = Path(os.getenv("PROXIES_PATH", CONFIG_DIR / "proxies.txt"))
