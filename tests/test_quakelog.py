import json

from quakelog.quality import run_checks
from quakelog.store import load, save
from quakelog.transform import parse_feeds, upsert

FELT = {
    "DateTime": "2026-10-21T11:58:36+00:00",
    "Coordinates": "-5.40,104.68",
    "Magnitude": "2.5",
    "Kedalaman": "3 km",
    "Wilayah": "Pusat gempa berada di darat 9 km utara Tanggamus",
    "Dirasakan": "II Tanggamus",
}
M5 = {
    "DateTime": "2026-10-21T07:44:15+00:00",
    "Coordinates": "-7.75,128.18",
    "Magnitude": "5.1",
    "Kedalaman": "96 km",
    "Wilayah": "62 km TimurLaut MALUKUBRTDAYA",
    "Potensi": "Tidak berpotensi tsunami",
}
FEEDS = {
    "autogempa": {"Infogempa": {"gempa": {**FELT, "Potensi": "Gempa ini dirasakan", "Shakemap": "x.mmi.jpg"}}},
    "gempaterkini": {"Infogempa": {"gempa": [M5]}},
    "gempadirasakan": {"Infogempa": {"gempa": [FELT]}},
}


def test_parse_normalizes_fields():
    events = parse_feeds(FEEDS)
    assert len(events) == 3
    e = events[1]
    assert e["event_id"] == "20261021T074415_-7.75_128.18"
    assert e["datetime_utc"] == "2026-10-21T07:44:15Z"
    assert (e["latitude"], e["longitude"], e["magnitude"], e["depth_km"]) == ("-7.75", "128.18", "5.1", "96")
    assert e["dirasakan"] == ""


def test_upsert_merges_same_event_across_feeds():
    archive = {}
    new = upsert(archive, parse_feeds(FEEDS), seen_at="2026-10-21T12:00:00Z")
    assert new == 2
    felt = archive["20261021T115836_-5.40_104.68"]
    assert felt["feeds"] == "autogempa;gempadirasakan"
    assert felt["shakemap"] == "x.mmi.jpg"  # tidak ditimpa nilai kosong dari feed lain
    assert felt["dirasakan"] == "II Tanggamus"
    # menjalankan ulang tidak menambah kejadian dan tidak mengubah first_seen
    assert upsert(archive, parse_feeds(FEEDS), seen_at="2026-10-21T12:15:00Z") == 0
    assert felt["first_seen_utc"] == "2026-10-21T12:00:00Z"


def test_store_roundtrip(tmp_path):
    archive = {}
    upsert(archive, parse_feeds(FEEDS), seen_at="2026-10-21T12:00:00Z")
    path = tmp_path / "gempa.csv"
    save(archive, path)
    assert load(path) == archive
    assert path.read_text().splitlines()[1].startswith("20261021T074415")  # urut waktu
    geo = json.loads((tmp_path / "gempa.geojson").read_text())
    assert len(geo["features"]) == 2
    first = geo["features"][0]
    assert first["geometry"]["coordinates"] == [128.18, -7.75]
    assert first["properties"]["magnitude"] == 5.1


def test_quality_flags_bad_rows():
    archive = {}
    upsert(archive, parse_feeds(FEEDS), seen_at="2026-10-21T12:00:00Z")
    assert run_checks(archive) == {}
    archive["20261021T074415_-7.75_128.18"]["magnitude"] = "12.0"
    assert run_checks(archive) == {"magnitudo harus di antara 0 dan 10": ["20261021T074415_-7.75_128.18"]}
