# FAZ 5 — BOQ, Makara ve Bonding Aksesuar Bütünlüğü

## Amaç

FAZ 5, sipariş rezervinin fiziksel bir sürekli kesim gibi modellenmesi, makara aşımının sayısal alanlarda kaybolması ve SVL miktarının `contains_svl` bayraklarından türetilmesi hatalarını birlikte kapatır.

## Makara planı sözleşmesi

- `DrumCut` yalnız gerçek kesintisiz güzergâh kesimlerini temsil eder.
- Sipariş/fire payı `ORDER_ALLOWANCE` olarak mevcut kurulum makaralarının boş kapasitesine dağıtılır.
- İşletme yedeği fire payından ayrıdır ve azami makara sınırını aşmayan özel yedek makaralara bölünür.
- Gerçek bir güzergâh kesimi azami makara uzunluğunu aşıyorsa kesim bölünmez ve aşırı yüklü sahte makara oluşturulmaz; kesim `unassigned_route_cuts` içinde fail-closed raporlanır.
- Geçerli planda her gerçek kesim tam bir kez atanır ve toplam yük sipariş miktarına eşittir.

Her makara şu sayısal muhasebeyi taşır:

- `route_cut_length_m`
- `order_allowance_m`
- `spare_stock_length_m`
- `rounding_reconciliation_m`
- `loaded_length_m`
- `capacity_balance_m`
- `remaining_capacity_m`
- `overload_m`
- `assignment_status`

Plan durumu veri kalitesinden bağımsızdır: `VALID`, `INCOMPLETE` veya `INVALID`.

## Bonding aksesuar sözleşmesi

Tek otorite minor/major section grafiği ve bağlantı topolojisidir. `contains_svl` yalnız legacy cache/uyum kontrolüdür.

- Aynı major section içindeki sınır: `MINOR_CROSS_BOUNDARY`
- Major section değişim sınırı: `MAJOR_GROUND_BOUNDARY`
- Cross sınırı: cyclic cross bağlantı, cross-bonding link box ve devre başına üç SVL kolu
- Major sınır: solid-ground bağlantı, grounding link box ve SVL yok

SVL seti ile bağımsız SVL polü ayrı sayılır. Procurement, SVL, raporlama ve kabul zinciri ortak `bonding_accessories.py` resolver'ını kullanır.

## Sentetik 20 km referansı

- Minor section: 21
- Major section: 7
- İç joint sınırı: 20
- Cross boundary: 14
- Major ground boundary: 6
- Devre: 2
- Joint: 120
- Cross-bonding link box: 28
- Grounding link box: 12
- Toplam link box: 40
- SVL seti: 28
- SVL polü: 84

Sipariş planı:

- Gerçek güzergâh kesimi: 126
- Kesim toplamı: 121.752 m
- Sipariş/fire payı: 2.423 m
- Toplam sipariş: 124.175 m
- Fiziksel makara: 126
- Aşım: 0 m
- Atanmamış kesim: 0

## Yayın kabulü

`tools/run_release_acceptance.py` paketlenmiş sentetik procurement çıktısını bağımsız olarak yeniden denetler. JSON, CSV ve XLSX aynı sayısal planı taşımak zorundadır. Aşağıdakiler yayın kapısını düşürür:

- makara aşımı,
- atanmamış gerçek kesim,
- tahsis edilmeyen sipariş miktarı,
- muhasebe artığı,
- yinelenen kesim ataması,
- bonding aksesuar grafiği çelişkisi,
- JSON/CSV/XLSX tutarsızlığı.

Eski v0.16.9.4.14 makara aşımı PASS iddiası eksiksiz sayısal kanıta dayanmadığından yeni otomatik kabul zincirinde tarihsel olarak geçersiz kılınır.

## Kapsam dışı

- SVL elektriksel boyutlandırma denklemlerinin değiştirilmesi
- Makara ağırlığı/çapı/taşıma sınırlarının üreticiye özgü ayrıntılı modeli
- Ek yeri optimizasyonu
- FAZ 6 fizik derinleştirmeleri

Proje şeması `0.16.4` olarak korunmuştur.
