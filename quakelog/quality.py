"""Cek kualitas arsip sebelum disimpan. Tiap cek mengembalikan event_id yang melanggar."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta


def _future(r: dict) -> bool:
    if not r["datetime_utc"]:
        return False  # sudah dilaporkan oleh cek kolom wajib
    try:
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return True
    return dt > datetime.now(UTC) + timedelta(hours=1)


def _number(key: str, ok: Callable[[float], bool]) -> Callable[[dict], bool]:
    """Cek angka pada kolom `key`. Nilai kosong dilewati karena sudah dilaporkan oleh cek kolom wajib."""

    def bad(r: dict) -> bool:
        if not r[key]:
            return False
        try:
            return not ok(float(r[key]))
        except ValueError:
            return True

    return bad


CHECKS = {
    "kolom wajib tidak boleh kosong": lambda r: (
        not all(r[k] for k in ("event_id", "datetime_utc", "latitude", "longitude", "magnitude", "depth_km"))
    ),
    "waktu kejadian tidak boleh di masa depan": _future,
    "lintang harus di antara -90 dan 90": _number("latitude", lambda v: -90 <= v <= 90),
    "bujur harus di antara -180 dan 180": _number("longitude", lambda v: -180 <= v <= 180),
    "magnitudo harus di antara 0 dan 10": _number("magnitude", lambda v: 0 < v < 10),
    "kedalaman tidak boleh negatif": _number("depth_km", lambda v: v >= 0),
}


def run_checks(archive: dict[str, dict]) -> dict[str, list[str]]:
    """Kembalikan {nama cek: [event_id bermasalah]} hanya untuk cek yang gagal."""
    failed = {}
    for name, bad in CHECKS.items():
        ids = [eid for eid, r in archive.items() if bad(r)]
        if ids:
            failed[name] = ids
    return failed
