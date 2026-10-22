"""Fetch: unduh tiga feed gempa BMKG dan simpan salinan mentahnya ke data/raw."""

import json
import logging
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://data.bmkg.go.id/DataMKG/TEWS"
FEEDS = ["autogempa", "gempaterkini", "gempadirasakan"]
RAW = Path("data/raw")
# User-Agent bawaan Python-urllib ditolak server BMKG (HTTP 403)
USER_AGENT = "quakelog/0.1 (+https://github.com/SulthanAndyno/quakelog)"

log = logging.getLogger(__name__)


def fetch_feed(name: str, attempts: int = 3) -> dict:
    for i in range(1, attempts + 1):
        try:
            req = urllib.request.Request(f"{BASE_URL}/{name}.json", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except (OSError, json.JSONDecodeError) as e:
            log.warning("gagal mengambil %s (percobaan %d/%d): %s", name, i, attempts, e)
            if i < attempts:
                time.sleep(5 * i)
    raise RuntimeError(f"feed {name} tidak dapat diambil")


def fetch_all(raw: Path = RAW) -> dict[str, dict]:
    """Ambil semua feed. Feed yang gagal dilewati; error hanya jika semuanya gagal."""
    raw.mkdir(parents=True, exist_ok=True)
    feeds = {}
    for name in FEEDS:
        try:
            feeds[name] = fetch_feed(name)
        except RuntimeError as e:
            log.error("%s", e)
            continue
        # salinan mentah disimpan agar riwayat git menjadi arsip feed asli
        (raw / f"{name}.json").write_text(json.dumps(feeds[name], ensure_ascii=False, indent=2) + "\n")
    if not feeds:
        raise RuntimeError("semua feed gagal diambil")
    return feeds
