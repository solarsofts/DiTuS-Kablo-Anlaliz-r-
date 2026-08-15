# DiTuS Kablo Analizör v0.16.9.4.38 — Engineering Canvas Zoom Calibration

Bu sürüm yalnız arayüz grafik görünümü / zoom-pan davranışını kalibre eder. Fizik, hesap, model ve veri tabanı motorları v0.16.9.4.37 ile byte-identical tutulmuştur.

## Değişiklikler

- Ortak `ZoomPanGraphicsView` için FIT/MANUAL görünüm sözleşmesi eklendi.
- Mouse-wheel ile manuel zoom başladıktan sonra scrollbar veya viewport resize olayının `fitInView()` ile zoom'u geri sıfırlaması engellendi.
- Zoom-out alt sınırı çizimin `fit-to-content` ölçeğidir; tüm çizim görünür olduktan sonra daha fazla küçültme yapılmaz.
- Zoom-in kontrollü 1.10 adımla ve fit ölçeğinin en çok 16 katına kadar yapılır.
- Pencere resize/maksimize yalnız görünüm FIT modundaysa yeniden sığdırır; MANUAL zoom korunur.
- Bonding uzun-hat şeması ilk açılışta tüm ağı overview olarak gösterir; kullanıcı wheel-up ile major/minor section ayrıntısına girebilir.
- Termal, profil, transient, güzergâh ve kablo kesiti QGraphicsView'ları aynı temel sözleşmeye bağlandı.
- Kablo-Kanal `InstallationCanvas` aynı FIT/MANUAL mantığına uyarlandı; mevcut cursor-centred pan/zoom davranışı korundu.
- `Görünüme Sığdır` / `Kesite Sığdır` komutları görünümü tekrar FIT moduna alır; `1:1` manuel görünüm olarak kalır.

## Motor kilidi

`src/ucd/calculations/` ve `src/ucd/models/` v0.16.9.4.37 ile byte-identicaldır. Bu sürümde hesap fiziği değişmemiştir.
