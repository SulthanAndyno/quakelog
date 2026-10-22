"""Jalankan satu siklus pengarsipan: python -m quakelog"""

import logging
import os
import sys
from datetime import UTC, datetime

from quakelog.fetch import fetch_all
from quakelog.quality import run_checks
from quakelog.store import load, save
from quakelog.transform import parse_feeds, upsert

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("quakelog")


def write_summary(feeds: list[str], fetched: int, new: int, total: int, failed: dict) -> None:
    """Tulis ringkasan operasional ke halaman run GitHub Actions (hanya saat berjalan di Actions)."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "## Ringkasan pengarsipan",
        "",
        f"- Feed berhasil diambil: {', '.join(feeds)}",
        f"- Kejadian di feed: {fetched}",
        f"- Kejadian baru: {new}",
        f"- Total arsip: {total}",
        f"- Cek kualitas gagal: {len(failed)}",
    ] + [f"  - {name}: {', '.join(ids)}" for name, ids in failed.items()]
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    seen_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    feeds = fetch_all()
    events = parse_feeds(feeds)
    archive = load()
    new = upsert(archive, events, seen_at)
    log.info("feed: %s, kejadian: %d, baru: %d, total arsip: %d", list(feeds), len(events), new, len(archive))

    failed = run_checks(archive)
    write_summary(list(feeds), len(events), new, len(archive), failed)
    if failed:
        for name, ids in failed.items():
            log.error("cek kualitas gagal: %s (%s)", name, ", ".join(ids))
        return 1  # arsip tidak disimpan agar data lama tetap valid
    save(archive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
