# DiTuS v0.16.8 — Fiziksel Motor Doğrulama ve Shadow Karşılaştırma

## 1. Amaç

v0.16.8, v0.16.7’de tamamlanan kapalı çevrim N-core/N-kılıf elektro-termal motoru üretim motoru yapmaz. Kilitli üretim IEC/bonding/nodal yolu ile fiziksel gölge yolu aynı proje snapshot’ından bağımsız çalıştırılır; farklar, numerik kapılar, fiziksel korunumlar, veri kökeni ve harici benchmark kanıtları tek denetim sonucunda birleştirilir.

Motor çalışma modu:

```text
SHADOW_VALIDATION
```

Yükseltme hedefi:

```text
PHYSICAL_PRIMARY
```

Varsayılan karar:

```text
HOLD_SHADOW
```

## 2. Karşılaştırılan sonuçlar

- IEC 60287 legacy minimum ampacity ↔ kapalı çevrim fiziksel ampacity
- Legacy 2D nodal ampacity ↔ kapalı çevrim fiziksel ampacity
- IEC tasarım akımı sıcaklığı ↔ en sıcak fiziksel kablo sıcaklığı
- Legacy 2D nodal Tmax ↔ fiziksel Tmax
- Legacy bonding λ1 ↔ global N-core/N-kılıf λ1
- Legacy ↔ fiziksel toplam kılıf metal kaybı
- Legacy ↔ fiziksel toplam core metal kaybı
- Açık-devre standing-voltage özeti ↔ çözülen sheath-to-earth düğüm gerilimi

Farklar tek başına PASS/FAIL sayılmaz. Her satırda açık neden kodu bulunur:

- `THERMAL_AND_LOSS_MODEL_CHANGED`
- `CURRENT_SHARING_AND_LOSS_FEEDBACK_CHANGED`
- `GEOMETRY_AND_HEAT_SOURCE_DISTRIBUTION_CHANGED`
- `ELECTROMAGNETIC_FEEDBACK_CHANGED`
- `NETWORK_SCOPE_CHANGED`
- `AC_RESISTANCE_AND_CURRENT_SHARING_CHANGED`
- `OPEN_CIRCUIT_PROFILE_VS_SOLVED_NODE_VOLTAGE`

Bu ayrım, gerçek model genişlemesini yazılım hatası gibi göstermemeyi; fakat açıklanamayan farkları da gizlememeyi sağlar.

## 3. Zorunlu numerik ve fiziksel kapılar

### Elektro-termal yakınsama

Aynı anda:

- sıcaklık sabit-nokta residual’ı,
- core akım değişimi,
- kılıf akım değişimi,
- aktif kayıp değişimi,
- elektromanyetik iki-yöntem anlaşması,
- bütün 2D bölgelerin yakınsaması

kontrol edilir.

### Bağımsız EM yöntem anlaşması

```text
GLOBAL_DIRECT_KKT
GLOBAL_SHEATH_SCHUR
```

için core akımı, kılıf akımı ve düğüm gerilimi farkları ayrı kapılardır.

### Korunum ve denklem residual’ları

- Devre/faz toplam akımı korunumu
- Kılıf/link-box/GCC düğüm KCL
- Kılıf dal gerilim denklemi
- Paralel core uçtan uca gerilim eşitliği
- Global denklem residual’ı
- Matris condition number

### Termal kapılar

- Bütün bölgelerin yakınsaması
- Enerji kapanışı
- Lineer denklem residual’ı
- En sıcak fiziksel kablonun bulunması
- Ampacity iç ve dış döngüsünün birlikte kapanması

## 4. Veri ve yönetişim kapıları

- Kablo-Kanal Düzeni veri bütünlüğü
- Fiziksel kablo parametre motoru kapsamı
- Hesap parametreleri ve kaynak kökeni
- Proje kaynak veri çelişkileri
- Zırh fiziği kapsamı
- Earth-return model kapsam uyarısı

Generic başlangıç projesinde Cu Milliken tel profili doğrulanmadığı ve legacy katsayı kaynakları etkin olduğu için `PHYSICAL_PARAMETER_SCOPE` ve `CALCULATION_PROVENANCE` bilinçli olarak blokelidir.

## 5. Harici yayımlanmış benchmark kayıtları

Paket, telif/lisanslı standart ve CIGRE dokümanlarındaki sayısal tabloları kopyalamaz. Aşağıdaki dört kanıt ailesi için izlenebilir dış kayıt gerekir:

1. `IEC60287_1_1_STEADY_STATE`
2. `IEC60287_1_3_PARALLEL_CURRENT`
3. `CIGRE_TB797_BONDING`
4. `CIGRE_TB880_RATING_TOOL`

Her kanıt:

- referans/vaka kimliği,
- PASS/FAIL,
- vaka sayısı,
- kanıt dokümanı,
- tercihen dosya hash’i

ile dışarıdan kaydedilebilir. Kanıt pakete gömülmediğinde durum `NOT_RUN` ve yükseltme kapısı blokelidir.

## 6. Yükseltme kararları

### `HOLD_SHADOW`

En az bir fiziksel/numerik/veri kapısı FAIL veya BLOCKED ise.

### `CONTROLLED_PILOT_CANDIDATE`

İç kapıların tamamı geçip yalnız yayımlanmış harici benchmark kanıtı bekliyorsa.

### `PHYSICAL_PRIMARY_ACCEPTANCE_READY`

Bütün blocking kapılar ve zorunlu dört harici benchmark ailesi PASS olduğunda. Bu statü dahi otomatik proje sonucu yazımı değildir; kontrollü sürüm kararı gerekir.

## 7. Değişmeyen üretim yolu

v0.16.8:

- proje `lambda1` değerini değiştirmez,
- IEC sonuçlarını değiştirmez,
- üretim nodal sonucunu değiştirmez,
- termal malzeme/kesit verisi yazmaz,
- engine run registry’ye sonuç yazmaz,
- proje JSON şemasını değiştirmez,
- mevcut raporlama sonuçlarını değiştirmez.

Proje şeması `0.16.4` olarak korunur.

## 8. Arayüz

Menü:

```text
Hesap → Fiziksel Motor Doğrulama ve Shadow Karşılaştırma…
```

Sekmeler:

- Legacy ↔ Fiziksel
- Kabul Kapıları
- IEC/CIGRE Benchmark
- İz, Kapsam ve Sınırlar

## 9. Sonraki kapı

v0.16.8 sonrası iki teknik yol vardır:

1. Lisanslı/izlenebilir IEC-CIGRE benchmark vaka setlerini dış kanıt paketi olarak bağlamak ve regresyonları tamamlamak.
2. Kullanıcının not ettiği interaktif **Kablo-Kanal Düzeni** geliştirmesine geçmek: trench/backfill/duct/polygon geometri ve termal malzeme kütüphanesi.

Fiziksel motor, benchmark kapıları kapanmadan `PHYSICAL_PRIMARY` yapılmaz.
