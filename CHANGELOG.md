# Changelog

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id-ID/1.1.0/).

## [0.1.0] - 2026-10-22

### Ditambahkan
- Pengambilan feed autogempa, gempaterkini, dan gempadirasakan dari BMKG dengan percobaan ulang.
- Penyeragaman format kejadian dan penggabungan kejadian yang sama dari feed berbeda.
- Arsip CSV yang idempoten dengan kolom first_seen_utc.
- Enam pengecekan kualitas data yang mencegah arsip rusak tersimpan.
- Workflow pengarsipan setiap 15 menit dengan commit otomatis dan ringkasan operasional.
- Workflow CI untuk lint dan test.
- Ekspor arsip ke GeoJSON dan halaman peta interaktif di GitHub Pages.
