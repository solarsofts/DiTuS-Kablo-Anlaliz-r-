# v0.16.9.2 — Kablo-Kanal Düzeni Kontur ve Mühendislik Çıktısı Teknik Notları

## Polygon köşe modeli

Özel termal bölge köşeleri `ThermalMaterialRegionData.vertices_m` içinde `[x_m, depth_m]` olarak saklanır. Köşe tutamaçları yalnız bu listeyi değiştirir; yeni bir termal solver veri yolu oluşturmaz.

Köşe ekleme işlemi varsayılan olarak en uzun kenarı seçer ve orta noktayı ekler. Köşe silme işlemi üç köşe altına düşmeyi engeller. Bu işlemler Qt'den bağımsız yardımcı fonksiyonlarla test edilir:

- `insert_material_region_vertex()`
- `remove_material_region_vertex()`

## Malzeme-ID görünümü

Malzeme görünümü aşağıdaki section bileşenlerini kimlikleriyle gösterir:

- doğal zemin,
- yatak,
- termal dolgu,
- seçilmiş dolgu,
- yüzey tabakası,
- koruma plakası,
- duct bank/grout,
- beton kanal,
- HDD grout,
- özel polygon bölgeleri.

Renkler yalnız görsel ayırma içindir. Termal hesapta kullanılan değer, proje termal malzeme kayıtlarındaki sayısal özelliklerdir.

## 2D sıcaklık konturu

Kontur, seçili section ve bağlı termal bölge için `solve_multiconductor_thermal()` gölge çözümünden alınır. Kullanılan alanlar:

- `x_edges_m`,
- `depth_edges_m`,
- `temperature_c`.

Çok ince ağlarda kanvas performansı için görsel hücre sayısı yaklaşık 3200 blokla sınırlandırılır. Blok sıcaklığı muhafazakâr görselleştirme amacıyla blok içindeki maksimum hücre sıcaklığıdır. Solver matrisi veya hesap ağı bu işlemle değiştirilmez.

Geometri veya kaynak değişikliğinde kontur önbelleği silinir. Kullanıcının yeni geometri için konturu yeniden çalıştırması gerekir.

## Mühendislik kesit paketi

`Mühendislik Kesit Çıktısı…` işlemi:

1. 300 dpi metadata taşıyan yüksek çözünürlüklü PNG,
2. section dataclass modeli ve kullanılan malzemeleri içeren UTF-8 JSON,
3. nesne bazlı UTF-8-BOM CSV

üretir.

CSV nesne türleri:

- `GEOMETRY`
- `CABLE`
- `DUCT`
- `MATERIAL_VERTEX`
- `HEAT_SOURCE`

Bu çıktı yeniden üretilebilir tasarım izi ve CAD/rapor entegrasyonu için ara formattır; kontrollü nihai rapor değildir.
