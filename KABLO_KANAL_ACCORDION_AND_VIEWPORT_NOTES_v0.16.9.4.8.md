# v0.16.9.4.8 — Kablo-Kanal Sağ Panel ve Görünüm Teknik Notları

## Sorun

v0.16.9.4.7'de sağ panel dikey splitter ile ikiye ayrılıyordu. Küçük ekran veya düşük pencere yüksekliğinde üst parametre paneli ile alt Devre Yerleşimi tablosu birbirini eziyor, splitter çizgisi aktif kontrol gibi görünmesine rağmen alt alan bazen erişilemez kalıyordu. `Devre Yerleşimini Aç` düğmesi de kullanıcı açısından ayrı ve belirsiz bir yönlendirme oluşturuyordu.

Çizim görünümünde ise wheel zoom Qt'nin otomatik anchor davranışına bırakılmıştı. Görüntü sağ kenara doğru kaçabiliyor ve kanvas salt okunur olduğu için kullanıcı sahneyi tekrar ortalayamıyordu.

## Uygulanan çözüm

### Akordeon panel

Sağ panel iki sabit başlık ve iki içerik alanından oluşur. Aynı anda yalnız bir içerik görünür:

```text
▾ Kesit ve Katman Ayarları
[üst parametre alanı]
▸ Devre / Kablo / Duct Yerleşimi
```

veya:

```text
▸ Kesit ve Katman Ayarları
▾ Devre / Kablo / Duct Yerleşimi
[sekme ve tablo alanı]
```

Bu çözüm splitter oranına bağlı değildir ve kullanılabilir yüksekliği seçilen bölüme verir. Açık bölüm `QSettings` ile saklanır.

### Salt okunur pan

`QGraphicsView.ScrollHandDrag` kullanılır. `setInteractive(False)` korunur; dolayısıyla scene item'ları seçilemez veya taşınamaz. Sol tuş sürüklemesi yalnız scroll/pan üretir.

### İmleç merkezli zoom

Wheel olayında:

1. İmlecin zoom öncesi sahne koordinatı alınır.
2. Görünüm ölçeklenir.
3. Aynı ekran pikselinin zoom sonrası sahne koordinatı alınır.
4. Aradaki fark kadar görünüm transformu düzeltilir.

Böylece imleç altındaki kesit noktası sabit kalır ve asimetrik sağa/sola büyüme engellenir.

## Mimari sınır

Bu sürüm yalnız `installation_designer_dialog.py` ekran davranışını ve paket sürüm metadata'sını değiştirir. Hesap motoru denklemleri veya proje veri alanları değiştirilmemiştir.
