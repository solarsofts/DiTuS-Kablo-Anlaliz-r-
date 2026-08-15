# v0.16.9.4.6 — Devre Bazlı Yerleşim ve Çizim Okunabilirliği

## Tasarım kararı

Ana mimari kilitlidir. Devre yerleşimi için yeni kalıcı proje sınıfı eklenmemiştir. Düzen, mevcut fiziksel kablo nesnelerinin koordinatlarından geri okunur ve aynı koordinatlara yazılır.

## Genel yerleşim ve bağımsız yerleşim ayrımı

### Genel yerleşim

Üst `Kablo Yerleşimi` paneli ortak formasyon, ortak derinlik, devre merkez aralığı ve paralel grup aralığıyla bütün devreleri birlikte yeniden kurar.

### Devre bazlı yerleşim

`Devre Yerleşimi` sekmesi her devre için şu girdileri taşır:

| Alan | Anlam |
|---|---|
| Bağımsız formasyon | TREFOIL, FLAT veya VERTICAL |
| X merkezi | Devrenin/paralel grup takımının yatay ağırlık merkezi |
| Referans derinliği | Devre faz gruplarının geometrik merkez derinliği |
| Faz merkez aralığı | A-B-C fiziksel merkez mesafesi |
| Paralel grup aralığı | Aynı devrede paralel formasyon merkezleri arası mesafe |

Uygulama işleminde yalnız ilgili devreye ait fiziksel kablolar taşınır. Diğer devrelerin koordinatları byte/sayısal olarak korunur.

## Formasyon matematiği

### FLAT

Faz merkezleri referans merkeze göre:

```text
A: (-s, 0)
B: ( 0, 0)
C: (+s, 0)
```

### VERTICAL

```text
A: (0, -s)
B: (0,  0)
C: (0, +s)
```

### TREFOIL

Eşkenar üçgen faz merkezleri kullanılır. Ofsetler, kullanıcının girdiği referans derinliğinin gerçek grup geometrik merkezi olması için sıfır ortalamaya normalize edilir.

Paralel formasyonlar yatay doğrultuda merkezlenerek yerleştirilir. Çakışma riski varsa mevcut fiziksel zarf kuralı faz veya paralel grup aralığını yalnız gerekli minimuma yükseltir ve kullanıcıya uyarı üretir.

## Devre formasyonunun geri okunması

Proje yeniden açıldığında formasyon ayrıca saklanan yeni bir enumdan değil, fiziksel A/B/C koordinatlarından çıkarılır:

- A üstte, B-C yaklaşık aynı derinlikteyse TREFOIL,
- düşey açıklık yatay açıklıktan baskınsa VERTICAL,
- diğer düzenlerde FLAT.

Bu nedenle mevcut proje şeması korunur.

## Bedding sand ve hendek davranışı

Devre bazlı mutlak derinlik uygulandığında `cable_group_bottom_locked` kapatılır. Bunun nedeni farklı devre derinliklerinin tek bir global taban kilidiyle yeniden kaydırılmasını önlemektir. Hendek derinliği ve alt genişliği, bütün fiziksel kabloları ve kum örtülerini içine alacak şekilde yalnız gerektiğinde genişletilir.

## Çizim etiketi politikası

- Normal görünümde yalnız faz harfi, ana katmanlar ve ana ölçüler gösterilir.
- Detay yazıları açıldığında devre/paralel/formasyon etiketleri leader çizgileriyle ayrı şeritlere yerleşir.
- Malzeme lejandı hendek hacminin üzerine basmaz.
- Kum üst ve alt örtüleri aynı metin satırında değil, ayrı düşey ölçüler olarak gösterilir.
