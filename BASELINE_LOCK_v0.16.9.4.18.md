# Baseline Lock — v0.16.9.4.18

Bu sürüm v0.16.9.4.17 FAZ 2 tabanı üzerinde FAZ 3.1 çalışma zamanı dayanıklılığı değişikliklerini içerir.

- Proje şeması: `0.16.4`.
- Üretici katalog verisi: paketlenmez.
- IEC sıcaklık düzeltmesi: 20 °C altı geçerli; yapay 0 °C sınırı yoktur.
- IEC termal tasarım akımı: sıfır kabul edilir.
- Güzergâh sonucu: senaryo × bölüm outcome matrisi.
- Durum modeli: tamamlanma ve mühendislik uygunluğu ayrı eksenlerdir.
- α legacy göçü: yalnız `PROJECT_CABLE_SNAPSHOT` ve `GENERIC_TEMPLATE`; manuel override korunur.
- Hesap/model dizinlerinin yayın hash kümesi: `ENGINE_BASELINE_v0.16.9.4.18.sha256` — 39/39 dosya.

v0.16.9.4.17 başlangıcına göre hesap/model alanında değişen veya eklenen dosyalar:

- `src/ucd/calculations/__init__.py`
- `src/ucd/calculations/application_database.py` (yalnız paket revizyonu)
- `src/ucd/calculations/bonding.py`
- `src/ucd/calculations/cable_physical_parameters.py`
- `src/ucd/calculations/cable_template_generator.py`
- `src/ucd/calculations/calculation_policy.py`
- `src/ucd/calculations/iec60287.py`
- `src/ucd/calculations/nodal_thermal.py`
- `src/ucd/calculations/primitive_cim.py`
- `src/ucd/calculations/result_status.py` (yeni)
- `src/ucd/calculations/thermal_optimization.py`
- `src/ucd/calculations/thermal_route.py`
- `src/ucd/calculations/transient_thermal.py`

FAZ 3.1 dışındaki hesap denklemleri ve proje/model şeması değiştirilmemiştir. VERTICAL/DUCT yerleşim kapsamı bu kilidin parçası değildir.
