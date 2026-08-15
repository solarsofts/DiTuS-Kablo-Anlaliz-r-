# v0.16.9.4.1 — Kablo-Kanal Düzeni Açılış Hotfix Teknik Notu

## Kök neden

`_build_ui()` yürütme sırası içinde görünüm düğmelerinin sinyal bağlantıları, `self.canvas = InstallationCanvas()` satırından önceydi. Python, bound method oluştururken `self.canvas` özelliğini hemen çözmeye çalıştığı için diyalog constructor aşamasında duruyordu.

## Müdahale

Önceki hatalı bağlantı:

```python
fit_section_button.clicked.connect(self.canvas.fit_to_section)
zoom_reset_button.clicked.connect(self.canvas.zoom_reset)
```

Güvenli bağlantı:

```python
fit_section_button.clicked.connect(
    lambda _checked=False: self.canvas.fit_to_section()
)
zoom_reset_button.clicked.connect(
    lambda _checked=False: self.canvas.zoom_reset()
)
```

Böylece `self.canvas`, sinyal bağlantısı kurulurken değil kullanıcı düğmeye bastığında çözülür. O zamana kadar canvas oluşturulmuş durumdadır.

## Regresyon koruması

`tests/test_installation_dialog_startup_order.py`, canvas oluşturulmadan önce doğrudan bound-method erişiminin yeniden eklenmesini engeller.
