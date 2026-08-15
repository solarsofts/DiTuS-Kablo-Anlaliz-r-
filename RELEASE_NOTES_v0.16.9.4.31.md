# DiTuS Kablo Analizör v0.16.9.4.31 — FAZ 7.1

## Test bootstrap ve paketleme

- `pyproject.toml` eklendi; `src/` paket yerleşimi ve pytest keşfi artık depo içinde açıkça tanımlı.
- `pytest` için `pythonpath = ["src"]` ve `testpaths = ["tests"]` tanımlandı. Temiz checkout'ta repo kökünden çıplak `python -m pytest` koleksiyonu artık `ucd` import hatası vermez.
- `run_tests.bat` içindeki elle `PYTHONPATH=%CD%\src` kancası kaldırıldı.
- `setup_venv.bat`, bağımlılıklardan sonra projeyi `pip install --no-deps -e .` ile editable kaydeder.
- `conftest.py` ile `sys.path` değiştiren gizli bootstrap yaklaşımı kullanılmadı.
- FAZ 7.1 regresyon testi, `PYTHONPATH` ortam değişkeni silinmiş alt süreçte gerçek pytest koleksiyonunu doğrular.

Bu sürüm FAZ 7.2 UI runtime test kapsamını, FAZ 7.3 orkestrasyon ayrıştırmasını ve FAZ 7.4 CI matrisini içermez.
