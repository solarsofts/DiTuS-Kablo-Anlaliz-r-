# DiTuS Kablo Analizör v0.16.9.4.20 — FAZ 4 Geometri Bağlaşımı

## Tek fiziksel geometri

- Termal route, bonding ve primitive ağ aynı bölge-kesit fiziksel x-y snapshot'ını tüketir.
- Faz geometrisi devre ve paralel grup bazında çözülür.
- Bütün grupları tek bir median `phase_spacing_m` değerine çökerten üretim davranışı kaldırıldı.
- `CableData.arrangement` ve global faz aralığı yalnız legacy fallback/cache olarak kaldı.

## Derinlik ve katmanlı hendek

- `burial_depth_m` en sığ aktif kablo ekseni olarak korunur.
- Homojen AUTO_IMAGE hesabı, kablo eksenleri sabitken hendek tabanı değişiminden etkilenmez.
- AUTO_MIXED_ZONE eşdeğer dolgu yarıçapı gerçek üst/alt/yan malzeme sınırlarından türetilir.
- Termal dolgu + doğal zemin + yatay genel üst dolgu içeren sentetik referans kesit analitik hızlı yolda kalır.
- Slab, tanımlı yeraltı suyu ve aktif özel malzeme poligonları `ANALYTIC_LAYERED_GEOMETRY_REQUIRES_NODAL` model-kapsam hatası üretir; fiziksel ret sayılmaz.

## Bonding bağlaşımı

- Bonding çalıştırıcısı geometri senkronizasyonunu ve route materialization'ı kendi içinde zorunlu yapar.
- Hedef devre/paralel grup için gerçek faz etiketli x-y koordinatları kullanılır.
- Güzergâh loop reaktansı tek rastgele bölge aralığından değil, bölge parçalarının uzunluk ağırlıklı geometrisinden hesaplanır.
- CUSTOM fiziksel geometri bonding ve primitive ağda doğrudan desteklenir.
- Termal analitik model-kapsam hatası, bonding için mevcut fiziksel güzergâhı silmez.

## Geriye uyumluluk

- Fiziksel kanal kesiti bulunmayan kanonik eski projeler `LEGACY_SCALAR` koşullu fallback ile açılmaya devam eder.
- Legacy scalar alanlar, kabul edilmiş fiziksel kesit varken üretim otoritesi değildir.

## Sentetik çıktılar

- Sentetik proje, katalog uygulama, bonding, nodal, rapor ve tedarik çıktıları yeni geometri/snapshot zinciriyle yeniden üretildi.
- Proje şeması `0.16.4` olarak korundu.
