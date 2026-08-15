# DiTuS Kablo Analizör v0.16.9.4.33

FAZ 7.2–7.4 test altyapısı kapanışı.

- Qt dışı `application_orchestration` katmanı eklendi.
- Termal ön işlem materialization/section-solve zinciri MainWindow'dan çıkarıldı.
- Üretim bonding electrothermal→global bonding→legacy diagnostic zinciri MainWindow'dan çıkarıldı.
- Headless orchestration regresyonları ve PySide6 offscreen gerçek pencere smoke testi eklendi.
- Windows/Linux, Python 3.11/3.12 GitHub Actions CI matrisi eklendi.
- CI çıplak `python -m pytest` ve `QT_QPA_PLATFORM=offscreen` kullanır; PYTHONPATH kancası yoktur.
- Proje veri şeması değişmedi: 0.16.4.

## Doğrulama
Paketleme ortamında 494 test PASS, 1 Qt-runtime testi PySide6 bulunmadığı için SKIP, 0 FAIL. Yayın bütünlüğü PASS ve engine baseline 52/52 dosyadır. Qt runtime testi CI'da PySide6 kurulumu ve offscreen platform ile zorunlu olarak çalışır.
