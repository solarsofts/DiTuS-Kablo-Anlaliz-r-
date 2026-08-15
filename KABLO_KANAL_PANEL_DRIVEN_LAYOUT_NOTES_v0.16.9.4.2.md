# Kablo-Kanal Düzeni — Sağ Panel Kontrollü Ölçekli Yerleşim

## Tasarım kararı

Kanvas artık veri giriş yüzeyi değildir. Çizim, gerçek kablo dış çapı ve metre cinsinden kanal ölçülerinden oluşturulan salt okunur mühendislik önizlemesidir. Model yalnız sağ panel, tablolar ve açık uygulama düğmeleri üzerinden değiştirilir.

Bu kararın amacı:

- tıklama ile beklenmeyen zoom/konum değişimini önlemek,
- sahne yeniden çizimi sırasında QGraphicsItem yaşam döngüsü hatalarını ortadan kaldırmak,
- kullanıcının sayısal proje girdisi ile çizimin aynı kaynaktan üretildiğini garanti etmek,
- gerçek ölçek, kablo zarfı ve kanal zarfı ilişkisinin okunmasını sağlamaktır.

## Sağ panel girdileri

### Kablo yerleşimi

- Formasyon
- Devre/hat sayısı
- Faz başına paralel kablo sayısı
- Faz sıraları
- Devre akımları
- Kablo merkez derinliği
- Kablo merkez aralığı
- Devre merkez aralığı
- Paralel grup merkez aralığı
- Duct satır/sütun sayısı
- Kablo dış çapı

Formasyon ve geometrik aralıklar mevcut kablo kimliklerini koruyarak anında uygulanır. Devre veya paralel sayısı değişikliği fiziksel nesne oluşturup sildiği için açık uygulama düğmesi kullanır.

### Hendek ve malzeme katmanları

- Kanal taban genişliği
- Toplam kazı derinliği
- Yan eğim H:V
- Bedding sand kalınlığı
- Thermal backfill/kablo çevresi yüksekliği
- Backfill/seçilmiş dolgu yüksekliği
- Kalan general backfill/üst dolgu
- Native soil/doğal zemin malzemesi
- Koruma plakası ve yüzey tabakası

## Ölçek ilkesi

- Scene ölçeği: 260 px/m.
- Kablo çizim çapı: `overall_diameter_mm / 1000 × scale_px_m`.
- Duct çizim çapı: `outer_diameter_m × scale_px_m`.
- Yalnız sıfıra yakın nesnelerin görünmez olmaması için 3 px güvenlik tabanı kullanılır; normal enerji kablolarında gerçek çap baskındır.
- Hendek ve kablolar aynı koordinat sistemiyle çizilir.

## Termal katman karşılığı

Görsel rol ile hesap malzemesi ayrıdır:

- Rol rengi kullanıcıya katman işlevini anlatır.
- `material_id`, ısıl özdirenç/iletkenlik kaydını belirler.
- Malzeme ID görünümü açıldığında kimlik ve ad görünür; rol rengi değişmez.
- Gölge 2D termal çözüm yalnız kullanıcı kabul edilmiş section geometrisini kullanır.

## Kapsam dışı

- Kanvas üzerinden serbest sürükleme
- Kanvas üzerinden polygon köşesi değiştirme
- Spacer/bims elemanının ayrı termal katı nesne olarak modellenmesi
- Warning tape/mesh'in ısıl eleman olarak çözülmesi

Spacer/bims bu sürümde düz formasyon merkez aralığının yapım yöntemi olarak açıklanır. Ayrı BOQ/çizim nesnesi sonraki kontrollü geliştirmeye bırakılmıştır.
