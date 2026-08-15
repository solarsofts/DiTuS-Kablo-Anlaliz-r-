# Baseline Lock — v0.16.9.4.17

Bu sürüm v0.16.9.4.16 yayın bütünlüğü tabanı üzerinde FAZ 2 katalog ve parametrik geometri değişikliklerini içerir.

- Proje şeması: `0.16.4`.
- Üretici katalog verisi: paketlenmez.
- Yerleşik içerik: yedi üretici-bağımsız `CONDITIONAL` jenerik şablon.
- Katman zinciri: tek geometri otoritesi.
- Dış çap: parametrik üreteç çıktısı.
- Malzeme ısıl özdirençleri: merkezi profil.
- Doğrulama kapıları: dış çap ve kg/km.
- Hesap/model dizinlerinin yayın hash kümesi: `ENGINE_BASELINE_v0.16.9.4.17.sha256` — 38/38 dosya.

v0.16.9.4.16 başlangıcına göre mevcut dosya değişiklikleri yalnız şunlardır:

- `src/ucd/calculations/application_database.py`
- `src/ucd/calculations/cable_library.py`
- `src/ucd/models/project.py`

Yeni dosya:

- `src/ucd/calculations/cable_template_generator.py`

Diğer mevcut hesap/model dosyaları başlangıç tabanıyla byte-identical kalır. Bu sürüm çözüm denklemi değişikliği değildir.
