"""Store: baca dan tulis arsip gempa dalam format CSV dan GeoJSON."""

import csv
import json
from pathlib import Path

from quakelog.transform import COLUMNS

ARCHIVE = Path("data/gempa.csv")


def load(path: Path = ARCHIVE) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {row["event_id"]: row for row in csv.DictReader(f)}


def save(archive: dict[str, dict], path: Path = ARCHIVE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(archive.values(), key=lambda r: (r["datetime_utc"], r["event_id"]))
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    save_geojson(rows, path.with_suffix(".geojson"))


def save_geojson(rows: list[dict], path: Path) -> None:
    """Tulis arsip sebagai GeoJSON FeatureCollection untuk peta di GitHub Pages."""
    features = [
        {
            "type": "Feature",
            # urutan koordinat GeoJSON adalah [bujur, lintang]
            "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
            "properties": {
                **{k: r[k] for k in COLUMNS if k not in ("latitude", "longitude")},
                "magnitude": float(r["magnitude"]),
                "depth_km": float(r["depth_km"]),
            },
        }
        for r in rows
    ]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False) + "\n")
