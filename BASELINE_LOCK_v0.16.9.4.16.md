# Baseline Lock — v0.16.9.4.16

Bu sürüm v0.16.9.4.15 kilitli tabanı üzerinde yalnız yayın veri bütünlüğü denetimini güvenilir hâle getirir.

- `src/ucd/calculations` ve `src/ucd/models`, `ENGINE_BASELINE_v0.16.9.4.15.sha256` ile byte düzeyinde doğrulanır.
- Proje şeması `0.16.4` olarak korunur.
- Yayın taraması genel desenler, kimlik metadata alanları ve SHA-256 regresyon parmak izlerinden oluşur.
- PDF metni ve metadata yüzeyleri `pypdf` ile fail-closed taranır.
- JSON/TXT/MD kabul belgeleri `tools/run_release_acceptance.py` tarafından otomatik üretilir; elle yazılmış PASS beyanı yetkili değildir.
