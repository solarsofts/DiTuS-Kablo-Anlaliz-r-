# Kurulum ve Fiziksel Kesit Veri Mimarisi — v0.16.3

## 1. Tasarım kararı

Önceki sürümlerde termal ve bonding motorları geometriyi kendi içinde Trefoil/Flat ve birkaç skaler aralık girdisinden üretmekteydi. Bu yaklaşım tek devre ön modellerinde kullanılabilir olsa da aşağıdakileri ortak ve izlenebilir biçimde temsil edemez:

- farklı faz sıralı çoklu devreler,
- faz başına paralel kablolar,
- asimetrik x-y konumları,
- duct bank slotları,
- devre bazlı farklı yükler,
- harici ısı kaynakları,
- aynı güzergâhta birden fazla fiziksel kesit.

v0.16.3 ile **kurulum geometrisinin sahibi solver değil, proje modelidir**.

## 2. Nesne hiyerarşisi

```text
InstallationDesignData
└── InstallationCrossSectionData[]
    ├── InstallationCircuitData[]
    ├── PhysicalCableData[]
    ├── DuctSlotData[]
    └── ExternalHeatSourceData[]
```

### InstallationCircuitData

Devre kimliği, görünen ad, faz sırası, toplam **RMS faz akımı**, legacy yük katsayısı alanı ve etkinlik durumunu taşır. Legacy `load_factor` proje dosyası uyumluluğu için korunur; kararlı durum akımını ölçeklemez.

### PhysicalCableData

Bir fiziksel tek damarlı kabloyu tanımlar. Devre/faz/paralel numarası, `x`, derinlik, duct slotu, kablo snapshot referansı ve RMS akım/açı override'ı saklanır. Legacy `load_factor` alanı dosya uyumluluğu için korunur ancak fiziksel kablo akımını çarpmaz.

### InstallationCrossSectionData

Kurulum tipi, formasyon etiketi, koordinat sistemi, bağlı termal bölge ID'leri, kaynak, notlar ve tüm fiziksel nesneleri taşır.

Koordinat sözleşmesi:

```text
x_m      : yatay eksen, kesit merkezinin sağı pozitif
 depth_m : zemin yüzeyinden aşağı doğru pozitif
birim    : metre
```

## 3. Hazır yerleşimler

Tasarımcı aşağıdaki başlangıç şablonlarını üretebilir:

- TREFOIL,
- FLAT,
- VERTICAL,
- DUCT_BANK.

Şablonlar nihai fiziksel model değildir. Oluşturulduktan sonra her kablo ayrı koordinat ve atama kaydı olarak saklanır. Kullanıcı özel formasyon için kabloları taşıyabilir veya tablo değerlerini doğrudan değiştirebilir.

## 4. Akım ön izlemesi

v0.16.3 akım paylaşımını çözmez. Yalnız veri kontrolü ve sonraki solver girdisinin görünür olması amacıyla:

1. devre toplam RMS faz akımı doğrudan alınır; legacy `load_factor` uygulanmaz,
2. aynı devre/fazdaki açık RMS akım override'ları ayrılır,
3. kalan akım override bulunmayan paralel kablolara eşit dağıtılır,
4. nominal A/B/C açıları sırasıyla `0°`, `-120°`, `+120°` atanır,
5. kablo bazlı açı override'ı varsa kullanılır.

Bu sonuç IEEE 60287-1-3/IEEE 575/P575 akım paylaşımı çözümü değildir. Eşitsiz paylaşım v0.16.5 genel primitive ağında çözülecektir.

## 5. Doğrulama kuralları

Kayıt sırasında aşağıdaki kontroller yapılır:

- kesit/devre/fiziksel kablo/duct slot ID tekilliği,
- geçerli A/B/C fazı ve faz sırası,
- devre başına faz bütünlüğü,
- fazlar arasında paralel kablo sayısı tutarlılığı,
- pozitif ve sonlu derinlik,
- kablo dış çapına göre fiziksel çakışma,
- duct slot tekil işgali,
- kablo-slot koordinat uyumu,
- negatif akım engeli; unity dışı legacy yük katsayısı için açık `IGNORED` uyarısı,
- harici ısı kaynağı yarıçapı, derinliği ve W/m değeri.

Hatalı taslak kullanıcı onayıyla saklanabilir; ancak workflow aşaması nihai hazır kabul edilmez.

## 6. Eski proje geçişi

Eski proje dosyasında fiziksel kesit yoksa her termal güzergâh bölgesi için ayrı başlangıç modeli mevcut skaler girdilerden üretilir. Duct bank slot eşleşmesi skaler kaynakta yoksa uydurulmaz ve kullanıcı tamamlamasına bırakılır. Kaynak ve solver bağı açıkça işaretlenir:

```text
source_reference     = LEGACY_PROJECT_PROJECTION
solver_coupling_mode = DESIGN_ONLY
```

Bu işlem veri kaybını önler, fakat eski skaler kabulleri saha doğrulanmış geometriye dönüştürmez.

## 7. Solver bağlama sözleşmesi

v0.16.3'ün güvenlik kuralı:

```text
Physical installation saved
!=
Physical installation used by solver
```

Mevcut çözücüler eski girişleriyle kilitlidir. Yeni model değiştiğinde ilgili sonuç kayıtları stale yapılır. Bir motor ancak aşağıdaki adaptörleri ve regresyonları tamamlandığında `solver_coupling_mode` değiştirir:

- fiziksel kablo → kayıp kaynağı,
- fiziksel kablo → analitik mutual thermal matrisi,
- fiziksel kablo → 2D mesh/ısı kaynağı,
- fiziksel kablo → primitive elektromanyetik eleman,
- devre/faz/paralel bilinmeyenleri → akım paylaşımı,
- minor section/bonding yolu → kılıf düğüm ve akım sonuçları.

## 8. Teknik referans kapsamı

### IEC 60287-1-2:2023

Tek damarlı kabloların çift devre düz formasyonunda metalik kılıf girdap kayıpları ve bonding durumları için fiziksel yerleşim önemlidir. Her iki uçtan bağlı sistemlerde dolaşım akımları ayrıca dikkate alınır.

### IEC 60287-1-3:2023

Her faz için herhangi sayıda paralel tek damarlı kabloyu, herhangi fiziksel düzende ve farklı kılıf bonding düzenleriyle ele alır. Bu kapsam, veri modelinin sabit üç iletken yerine N fiziksel kabloyu temsil etmesi kararının ana dayanağıdır.

### IEEE 575-2014 / P575

IEEE 575 kılıf gerilim ve akımlarını sınırlamak için bonding yöntemlerini ve hesap yaklaşımlarını açıklar. 2014 baskısı `Inactive-Reserved` durumundadır; güncel revizyon çalışması P575 olarak izlenmelidir. v0.16.3 yalnız veri hazırlığı sağlar.

### CIGRE TB 797

Bonding sistemi tasarımında proje özelindeki kablo, kurulum ve sistem parametrelerini; indüklenen gerilim/akım hesaplarının model ve formüllerini ele alır. Tek ortak geometri modeli bu izlenebilirlik için gereklidir.

### IEC 60853-3:2002

Kısmi toprak kuruması altında çevrimsel rating kapsamıdır. Gruplar arası mesafe ve özel backfill koşulları uygulama sınırları taşır. Bu nedenle dry-out transient katmanı, çoklu kablo kararlı kayıp/sıcaklık başlangıcı doğrulandıktan sonra bağlanacaktır.

## 9. v0.16.4 kabul kapısı

- bütün fiziksel kablolar ortak termal alana ayrı kaynak olarak girer,
- iletken/dielektrik/kılıf/zırh kayıpları kablo bazında izlenir,
- farklı devre yükleri sonucu etkiler,
- analitik mutual matrisi ve 2D çözüm karşılaştırılır,
- sonuçlar kablo/devre/faz/paralel seviyesinde raporlanır,
- v0.16.2.6 tek devre regresyonları korunur.
