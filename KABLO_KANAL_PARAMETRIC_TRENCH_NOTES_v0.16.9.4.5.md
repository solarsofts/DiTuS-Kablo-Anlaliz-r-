# v0.16.9.4.5 — Parametrik Hendek Mühendislik Modeli

## Tasarım amacı

Kablo-Kanal Düzeni ekranı serbest çizim aracı değildir. Section için ölçekli ve tekrar üretilebilir inşaat kesiti üretir. Girdiler sağ panelden alınır; çizim yalnız sonucu gösterir.

## Koordinat sistemi

- `x`: hendek merkezinden yatay metre
- `depth`: bitmiş zemin kotundan aşağı doğru pozitif metre
- kablo merkezi, duct merkezi ve tüm katman kotları aynı metrik koordinat sistemindedir
- ekrandaki zoom yalnız görünümü değiştirir; fiziksel oranları değiştirmez

## Kablo zarfı

Kablo dış yarıçapı:

```text
r = overall_diameter / 2
```

Etkin fiziksel kablolar için:

```text
cable_left   = min(x_i - r)
cable_right  = max(x_i + r)
cable_top    = min(depth_i - r)
cable_bottom = max(depth_i + r)
```

Yatak kumu zarfı:

```text
bedding_left   = cable_left  - side_clearance
bedding_right  = cable_right + side_clearance
bedding_top    = cable_top   - top_cover
bedding_bottom = cable_bottom + bottom_cover
```

Tabana kilitli modda:

```text
deepest_cable_center = trench_depth - bottom_cover - r
```

olacak şekilde bütün kablolar aynı düşey miktarda ötelenir.

## Katman sırası

Doğrudan gömülü başlangıç modeli üstten alta:

1. Native soil / doğal zemin — hendek dışı ortam
2. General backfill / genel üst dolgu
3. Selected backfill / seçilmiş dolgu
4. Thermal backfill / termal dolgu
5. Bedding sand / yatak kumu zarfı
6. Hendek tabanı

Uyarı ağı ve bandı hacimsel termal malzeme değil, inşaat/işaretleme elemanıdır. Koruma plakası mevcut modelde ayrı katı bölge olarak kalır.

## Derinlik tanımları

Ekran aşağıdaki değerleri birbirinden ayırır:

- en üst kablonun dış yüzey derinliği,
- en üst kablo merkez derinliği,
- yatak kumu üst kotu,
- toplam hendek derinliği.

Formasyon referans derinliği, taban kilidi açıkken kullanıcı tarafından değiştirilmez; hendek derinliği ve alt kum örtüsü kablo grubunun nihai kotunu belirler.

## Flat formasyon spacer/bims

Flat formasyonda A-B ve B-C aralıkları gerçek kablo dış yüzeyleri arasındaki boşluktan hesaplanır. Spacer/bims çizimi:

- gerçek boşluğu aşmaz,
- kullanıcının tanımladığı genişlik/yükseklikle gösterilir,
- elektriksel veya termal malzeme modeli yerine bu aşamada inşaat yerleşim göstergesidir.

Spacer malzemesinin termal etkisi daha sonra kaynaklı ayrı malzeme nesnesiyle ele alınmalıdır; bu sürümde termal solver girdisine eklenmez.

## Kablo konstrüksiyon görünümü

Proje kablosu katmanlarında `outer_diameter_mm` bulunduğunda çizim en büyükten en küçüğe konsantrik halkalar üretir. Katman verisi yoksa yalnız gerçek toplam dış çap ve faz tanımlama halkası gösterilir. Eksik katman geometrisi uydurulmaz.

## Solver sınırı

Yeni geometri yalnız Kablo-Kanal editöründe ve mevcut gölge fiziksel kesit bağlantısında kullanılır. Kilitli üretim IEC, bonding ve nodal hesap yolları değiştirilmemiştir.
