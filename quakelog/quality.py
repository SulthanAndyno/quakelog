"""Cek kualitas arsip sebelum disimpan. Tiap cek mengembalikan event_id yang melanggar."""

from datetime import UTC, datetime, timedelta


def _future(r: dict) -> bool:
    dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    return dt > datetime.now(UTC) + timedelta(hours=1)


CHECKS = {
    "kolom wajib tidak boleh kosong": lambda r: (
        not all(r[k] for k in ("event_id", "datetime_utc", "latitude", "longitude", "magnitude", "depth_km"))
    ),
    "waktu kejadian tidak boleh di masa depan": _future,
    "lintang harus di antara -90 dan 90": lambda r: not -90 <= float(r["latitude"]) <= 90,
    "bujur harus di antara -180 dan 180": lambda r: not -180 <= float(r["longitude"]) <= 180,
    "magnitudo harus di antara 0 dan 10": lambda r: not 0 < float(r["magnitude"]) < 10,
    "kedalaman tidak boleh negatif": lambda r: float(r["depth_km"]) < 0,
}


def run_checks(archive: dict[str, dict]) -> dict[str, list[str]]:
    """Kembalikan {nama cek: [event_id bermasalah]} hanya untuk cek yang gagal."""
    failed = {}
    for name, bad in CHECKS.items():
        ids = [eid for eid, r in archive.items() if bad(r)]
        if ids:
            failed[name] = ids
    return failed
