# DiTuS BOQ/BOM/RFQ ve Makara Planlama Motoru

## 1. Veri kaynağı

Tedarik çıktıları bağımsız elle doldurulan listeler değildir. Motor aşağıdaki proje nesnelerinden türetir:

```text
ProjectData
├── CableData ve değişmez katalog snapshot'ı
├── RouteSection ve aktif kablo atamaları
├── BondingSystemData: node, joint, link box, SVL, lead
├── ThermalDesignData: bölge ve kesit geometrisi
└── ProcurementData: paylar, yedekler ve gerekçeli override'lar
```

Hesap motorunun ürettiği sonuçlar veya proje geometrisi raporlama sırasında değiştirilmez.

## 2. BOQ, BOM ve RFQ ayrımı

- **BOQ:** miktar, metraj ve birim odaklı görünüm.
- **BOM:** malzeme/ekipman sınıfı ve teknik kırılım.
- **RFQ:** aynı kalemlerin tedarikçiye gönderilecek teknik tanımı, istenecek belgeler ve teklif alanları.

Üç görünüm aynı `ProcurementLine` kaydını kullanır; miktarların farklı dosyalarda ayrışması engellenir.

## 3. Miktar izi ve kullanıcı düzeltmesi

Her kalem:

- otomatik miktar,
- nihai miktar,
- birim,
- kaynak nesne,
- formül/dayanak,
- veri durumu,
- kullanıcı override gerekçesi

alanlarını taşır. Override otomatik değeri silmez. Bu sayede örneğin 12 otomatik termination üzerine 2 işletme yedeği eklenmesi izlenebilir.

## 4. Kablo metrajı

Tek damarlı kablo için temel uzunluk:

```text
Σ(bölüm uzunluğu × 3 faz × aktif devre × paralel kablo/faz)
```

Buna termination ve joint kuyrukları; ardından montaj, fire ve yedek oranları eklenir. Sonuçlar üç ayrı gösterge olarak tutulur:

- net güzergâh uzunluğu,
- montajlı tek damarlı kablo uzunluğu,
- sipariş tek damarlı kablo uzunluğu.

## 5. Joint, termination, link box ve SVL

- Termination adedi bonding grafiğindeki termination düğümlerinden türetilir.
- Joint adedi sectionalizing/straight-joint düğümlerinden türetilir.
- Link box adedi link-box nesnelerinden ve devre sayısından üretilir.
- SVL adedi SVL içeren link box × faz × devre yapısından türetilir.

Bu değerler tek damarlı aksesuar adedidir. Üç fazlı kutu adedi ile tek fazlı SVL eleman adedi ayrı birimlerle gösterilir.

## 6. Makara/kesim algoritması

Bonding minor-section uzunlukları güzergâh uzunluğuyla uyumluysa her devre/faz/paralel yol için kesim listesi oluşturulur. Uyumlu değilse güzergâh bazlı kesimler ve açık uyarı üretilir.

Kesimler:

1. büyükten küçüğe sıralanır,
2. mevcut makaralarda ilk uygun boşluğa yerleştirilir,
3. sığmazsa yeni makara açılır,
4. sipariş yedeği ayrı `RESERVE` kesimi olarak görünür tutulur.

Bu plan teklif ve lojistik başlangıcıdır. Üretici azami brüt ağırlığı, makara çapı, fabrika üretim boyu, sevkiyat ve çekim planı ayrıca kontrol edilir.

## 7. İnşaat metrajı

İnşaat kalemleri isteğe bağlıdır. Hendek kazısı ve termal dolgu hacmi termal kesit genişliği, derinliği ve bölge uzunluğundan türetilir. Şev, kabarma, sıkışma, nakliye ve satın alma yoğunluğu varsayılan olarak dahil edilmez; RFQ notlarında açıkça belirtilir.

## 8. Durum politikası

Tedarik çıktısı teknik uygunluk veya satın alma onayı değildir. Başlıca durumlar:

- `CONFIRMED_PROJECT_DATA`
- `CONDITIONAL_PROJECT_DATA`
- `ENGINEERING_ASSUMPTION`

Kablo katalog verisi doğrulanmış olsa bile joint/termination arayüzü, SVL MCOV/TOV/enerji sınıfı, link box IP sınıfı ve saha metrajı ayrıca teyit edilmelidir.

## 9. Çıktı ve okunabilirlik

DOCX, PDF, HTML ve XLSX'te koyu lacivert başlıkların yazısı beyazdır. XLSX içinde filtre, freeze-pane, metin kaydırma ve teklif doldurma alanları vardır. JSON tam izlenebilir veri paketidir; CSV dış sistem entegrasyonu içindir.
