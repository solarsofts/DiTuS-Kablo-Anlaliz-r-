# FAZ 7 — Test altyapısı kapanışı (v0.16.9.4.33)

## 7.1 — çıplak pytest
`pyproject.toml` paket/import sözleşmesi korunur; `run_tests.bat` PYTHONPATH hilesine ihtiyaç duymaz.

## 7.2 — çalışma zamanı UI kapsamı
Kritik hesap sıralaması Qt sınıfından ayrıldı. `ucd.calculations.application_orchestration` Qt bağımlılığı olmadan termal ön işlem ve üretim bonding zincirini çalıştırır. MainWindow bu headless sözleşmeyi çağırır. PySide6 mevcut ortamlarda offscreen gerçek MainWindow construction smoke testi çalışır; CI'da `QT_QPA_PLATFORM=offscreen` zorunludur.

## 7.3 — main_window sınırı
Tam bir UI yeniden yazımı yapılmadı. Bunun yerine testte yakalanmış iki kritik iş mantığı — route materialization/section thermal sequencing ve production electrothermal→bonding→legacy diagnostic sequencing — hesap katmanına taşındı. UI'nın sorumluluğu precheck/consent, status persistence ve presentation olarak daraltıldı. Yeni iş mantığı MainWindow içine eklenmemelidir; headless orchestration katmanına eklenmelidir.

## 7.4 — CI
`.github/workflows/ci.yml` Windows + Linux ve Python 3.11 + 3.12 matrisi kullanır. PySide6 offscreen çalışır. CI `python -m pytest` çağırır ve PYTHONPATH enjeksiyonu kullanmaz.
