# DiTuS Kablo Analizör v0.16.9.4.37 — Responsive UI / Thermal Viewport Fix

Bu sürüm v0.16.9.4.35 üzerinde arayüz yerleşim düzeltmesidir. Fizik modelleri ve
proje şeması değiştirilmemiştir; proje şeması `0.16.4` kalır.

## Pencere yerleşimi

- `ucd.ui.window_layout` artık ekranı **maksimum boyut kilidi** olarak kullanmaz.
  Önceki `setMaximumSize(availableGeometry)` yaklaşımı kaldırıldı; kullanıcı tüm
  çalışma pencerelerini serbestçe büyütebilir ve maksimize edebilir.
- İlk pencere boyutu aktif monitörün `availableGeometry()` alanı, pencerenin
  gerçek `sizeHint()` değeri ve yoğunluk sınıfından birlikte çözülür.
- Uygulama geneline `ResponsiveWindowManager` eklendi. Ana pencereden veya başka
  bir diyalog içinden açılan üst düzey QDialog/QMainWindow örnekleri ilk Show
  olayında aynı sığdırma yoluna girer. Böylece unutulan yardımcı modüller ekran
  dışına taşamaz.
- Monitör değiştirme ve maximize → normal dönüşünde pencere yalnız görünür alana
  geri çekilir; kullanıcının normal pencere boyutu yeniden dayatılmaz.
- Başlangıç ekranındaki `setFixedSize(620, 500)` kaldırıldı.
- Kablo-Kanal düzeni iç minimumları küçültüldü; sağ panel ve accordion içerikleri
  düşük çözünürlükte pencereyi büyütmeye zorlamaz.
- `StageHostFrame` gövdesi kaydırılabilir hale getirildi. Modül içeriği yüksek olsa
  bile üst aşama bilgisi ve alt Önceki/Önerilen/Sonraki/Akıştan çık kontrolleri
  erişilebilir kalır.

## 2D termal görünüm

- Uzun başlık ve sonuç özeti artık `itemsBoundingRect()` genişliğini büyütüp termal
  alanı küçültmez; metinler belirli genişlikte sarılır ve çizim için kontrollü
  kompozisyon sınırı kullanılır.
- Fiziksel kablo dış çapı gerçek ölçekte çizilmeye devam eder. Uzak alan ölçeğinde
  kablo birkaç piksele düştüğünde yalnız görünürlük amacıyla transformdan bağımsız
  bir halo eklenir; halo fiziksel çap olarak kullanılmaz.
- Devre/faz etiketleri zoom seviyesinde kaybolmaması için ekran ölçeğinden bağımsız
  çizilir; kablo geometrisi diğer katmanların üstünde tutulur.
- Termal ekran yardım metni kısaltıldı; grafik için daha fazla dikey alan bırakıldı.
- `Görünüme Sığdır` komutu eklendi ve pencere boyutu değiştiğinde termal kesit yeni
  viewport'a otomatik yeniden sığdırılır.

## Motor kilidi

v0.16.9.4.35'e göre `src/ucd/models` byte-identical'dır. Hesap tarafındaki tek
sürüm kaynaklı fark uygulama veri tabanı paket revizyonunun `.36` olmasıdır;
v0.16.9.4.35'te Claude tarafından yapılan katsayı/provenance değişiklikleri aynen
korunmuştur.
