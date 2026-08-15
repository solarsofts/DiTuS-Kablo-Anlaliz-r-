# FAZ 7.1 — pytest bootstrap ve paketleme sınırı

Sürüm: 0.16.9.4.31

## Karar

Test import yolu için `conftest.py` içinde `sys.path` değiştiren gizli bir kanca kullanılmaz.
Depo `src/` yerleşimini `pyproject.toml` ile açıkça tanımlar. Aynı dosyadaki pytest ayarı
`pythonpath = ["src"]` kullandığı için, pytest kurulu bir temiz checkout'ta repo kökünden
`python -m pytest` veya `pytest` doğrudan koleksiyon yapabilir.

Geliştirme sanal ortamında `setup_venv.bat`, bağımlılıklardan sonra projeyi `pip install
--no-deps -e .` ile editable olarak kaydeder. Böylece uygulama/test araçları yalnız çalışma
dizinine veya elle kurulmuş `PYTHONPATH` değişkenine bağımlı değildir.

`run_tests.bat` içindeki manuel `PYTHONPATH=%CD%\\src` kaldırılmıştır. Bu script artık gerçek
kullanıcı/CI davranışını saklamaz.

## Kapsam

Bu faz yalnız test keşfi/paket bootstrap katmanını değiştirir. PySide6 çalışma-zamanı testleri,
UI iş mantığının ayrıştırılması ve CI matrisi FAZ 7.2–7.4 kapsamındadır.
