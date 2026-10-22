"""Transform: ubah isi feed BMKG menjadi baris arsip yang seragam, lalu gabungkan ke arsip."""

from datetime import datetime

COLUMNS = [
    "event_id",
    "datetime_utc",
    "latitude",
    "longitude",
    "magnitude",
    "depth_km",
    "wilayah",
    "potensi",
    "dirasakan",
    "shakemap",
    "feeds",
    "first_seen_utc",
]


def parse_event(raw: dict, feed: str) -> dict:
    dt = datetime.fromisoformat(raw["DateTime"])
    lat, lon = (float(x) for x in raw["Coordinates"].split(","))
    return {
        # BMKG tidak memberi ID kejadian, jadi ID dibentuk dari waktu dan koordinat
        "event_id": f"{dt:%Y%m%dT%H%M%S}_{lat:.2f}_{lon:.2f}",
        "datetime_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latitude": f"{lat:.2f}",
        "longitude": f"{lon:.2f}",
        "magnitude": f"{float(raw['Magnitude']):.1f}",
        "depth_km": raw["Kedalaman"].removesuffix("km").strip(),
        "wilayah": raw.get("Wilayah", "").strip(),
        "potensi": raw.get("Potensi", "").strip(),
        "dirasakan": raw.get("Dirasakan", "").strip(),
        "shakemap": raw.get("Shakemap", "").strip(),
        "feeds": feed,
    }


def parse_feeds(feeds: dict[str, dict]) -> list[dict]:
    events = []
    for name, payload in feeds.items():
        gempa = payload["Infogempa"]["gempa"]
        for raw in gempa if isinstance(gempa, list) else [gempa]:
            events.append(parse_event(raw, name))
    return events


def upsert(archive: dict[str, dict], events: list[dict], seen_at: str) -> int:
    """Gabungkan kejadian ke arsip. Nilai kosong tidak menimpa nilai lama. Mengembalikan jumlah kejadian baru."""
    new = 0
    for e in events:
        row = archive.get(e["event_id"])
        if row is None:
            archive[e["event_id"]] = {**e, "first_seen_utc": seen_at}
            new += 1
            continue
        for k, v in e.items():
            if k == "feeds":
                row["feeds"] = ";".join(sorted(set(row["feeds"].split(";")) | {v}))
            elif v:
                row[k] = v
    return new
