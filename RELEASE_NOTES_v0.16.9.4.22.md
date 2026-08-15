# DiTuS Kablo Analizör v0.16.9.4.22 — FAZ 5 Procurement Integrity

## Makara ve sipariş rezervi

- Sipariş/fire rezervinin tek, kesintisiz `ORDER_RESERVE` kesimi olarak oluşturulması kaldırıldı.
- Fire payı mevcut kurulum makaralarının boş kapasitelerine dağıtılıyor.
- İşletme yedeği ayrı ve azami uzunluğu aşmayan stok makaraları olarak modelleniyor.
- Gerçek güzergâh kesimi azami makaradan uzunsa sahte aşırı yüklü makara üretilmiyor; plan fail-closed kalıyor.
- Kapasite bakiyesi, kalan kapasite ve aşım ayrı sayısal alanlarda raporlanıyor.
- Makara planının fiziksel durumu genel proje veri durumundan ayrıldı.

## Bonding aksesuarları

- Link-box ve SVL miktarları ortak bonding accessory graph resolver'ından türetiliyor.
- Major-section sınırları solid-ground, minor iç sınırlar cyclic cross olarak doğrulanıyor.
- Cross-bonding ve grounding link-box miktarları ayrı raporlanıyor.
- SVL seti ve bağımsız SVL polü ayrı sayılıyor.
- Sentetik 20 km grafiğindeki altı major sınır düzeltilip bütün bonding/SVL/tedarik çıktıları yeniden üretildi.

## Sentetik 20 km sonuçları

- Makara: 126
- Sipariş/fire payı: 2.423 m
- Toplam aşım: 0 m
- Atanmamış kesim: 0
- Cross-bonding link box: 28
- Grounding link box: 12
- SVL seti/polü: 28/84
- Joint: 120
- Kablo snapshot: `SNAP-3DF6982A5722`

## Kabul zinciri

- Paketlenmiş procurement JSON/CSV/XLSX çıktıları sayısal olarak bağımsız denetleniyor.
- Makara aşımı veya bonding accessory graph çelişkisi yayın kapısını düşürüyor.
- Kabul TXT/MD belgeleri yapılandırılmış JSON sonucundan otomatik üretiliyor.
- v0.16.9.4.14 içindeki doğrulanmamış makara aşımı PASS iddiası tarihsel düzeltme notuyla geçersiz kılındı.

Proje şeması `0.16.4` olarak korunmuştur.
