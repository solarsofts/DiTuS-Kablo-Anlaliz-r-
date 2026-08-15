# Baseline Lock — v0.16.9.4.19

Bu sürüm v0.16.9.4.18 FAZ 3.1 tabanı üzerinde FAZ 3.2 yerleşim/model-kapsam değişikliklerini içerir.

- Proje şeması: `0.16.4`.
- VERTICAL: analitik termal, bonding ve primitive fallback desteği.
- Derinlik anlamı: en sığ aktif kablo ekseni.
- DUCT_BANK: kurulum tipi; faz formasyonu değildir.
- Otomatik analitik T4: yalnız `DIRECT_BURIED`.
- DUCT_BANK/HDD/CONCRETE_TROUGH/TUNNEL: nodal veya kaynaklandırılmış manuel T4.
- Model-kapsam hataları: bölüm-özgü ve `physical_rejection=False`.
- CUSTOM: explicit x-y geometri; koordinatsız kullanım fail-closed.
- Sessiz Flat normalizasyonu kaldırılmıştır.
- Hesap/model yayın hash kümesi: `ENGINE_BASELINE_v0.16.9.4.19.sha256`.

v0.16.9.4.18'e göre hesap/model alanında değişen veya eklenen dosyalar:

- `src/ucd/calculations/application_database.py` — paket revizyonu
- `src/ucd/calculations/bonding.py`
- `src/ucd/calculations/cable_channel_templates.py`
- `src/ucd/calculations/cable_template_generator.py` — paket revizyonu
- `src/ucd/calculations/iec60287.py`
- `src/ucd/calculations/installation.py`
- `src/ucd/calculations/installation_coupling.py`
- `src/ucd/calculations/phase_geometry.py` — yeni
- `src/ucd/calculations/primitive_cim.py`
- `src/ucd/calculations/thermal_resistance.py`
- `src/ucd/calculations/thermal_route.py`

Fiziksel kanal x-y geometrisinin bonding ağına tam aktarımı, duct analitik T4 denklemleri ve tek fazlı dönüş yolu modeli bu kilidin kapsamında değildir.
