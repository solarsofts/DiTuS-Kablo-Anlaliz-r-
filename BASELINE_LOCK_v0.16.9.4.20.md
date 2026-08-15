# Baseline Lock — v0.16.9.4.20

Bu sürüm v0.16.9.4.19 FAZ 3.2 tabanı üzerinde FAZ 4 geometri bağlaşımı değişikliklerini içerir.

- Proje şeması: `0.16.4`.
- Geometri otoritesi: bölgeyle eşlenmiş fiziksel InstallationCrossSectionData x-y/malzeme modeli.
- Derinlik: en sığ aktif kablo ekseni.
- AUTO_IMAGE: homojen zemin image-method.
- AUTO_MIXED_ZONE: indirgenebilir katmanlı hendek hızlı yolu.
- Slab/su/özel poligon: model-kapsam hatası, `physical_rejection=False`.
- Faz geometri çözümü: devre/paralel grup bazında.
- Bonding ve primitive ağ: faz etiketli explicit x-y güzergâh geometrisi.
- Legacy scalar projeler: koşullu fallback.
- Bayatlık: mevcut engine-run fingerprint/staleness altyapısı.
- Hesap/model yayın hash kümesi: `ENGINE_BASELINE_v0.16.9.4.20.sha256`.

v0.16.9.4.19'a göre hesap/model alanında değişen veya eklenen dosyalar:

- `src/ucd/calculations/__init__.py`
- `src/ucd/calculations/application_database.py` — paket revizyonu
- `src/ucd/calculations/bonding.py`
- `src/ucd/calculations/cable_template_generator.py` — paket revizyonu
- `src/ucd/calculations/iec60287.py`
- `src/ucd/calculations/installation_coupling.py`
- `src/ucd/calculations/primitive_cim.py`
- `src/ucd/calculations/project_geometry_runtime.py` — yeni
- `src/ucd/calculations/shadow_validation.py`
- `src/ucd/calculations/thermal_route.py`
- `src/ucd/models/project.py`

FAZ 4.2 analitik-nodal sonuç otoritesi, eşit olmayan kayıp vektörü ve tam çok-devre elektromanyetik bağlaşım bu kilidin kapsamında değildir.
