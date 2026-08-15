# Gerçek Katalog ve Aday Seçim Motoru — v0.15

## 1. Tasarım ilkesi

Katalog satırı bir **ön eleme girdisidir**; proje tasarım sonucu değildir. Bir kablonun katalogda belirli koşullarda taşıdığı akım, başka toprak, derinlik, yerleşim, devre sayısı ve bonding düzenindeki ampacity yerine kullanılamaz.

```text
Katalog satırı
→ gerilim/malzeme/kesit filtresi
→ referans ampacity ön elemesi
→ ön gerilim düşümü
→ kullanıcı seçimi
→ immutable project snapshot
→ gerçek proje hesap zinciri
```

## 2. Ayrı veri katmanları

`CableCatalogRecord` üç ayrı veri grubunu taşır:

- `catalog_dimensions`: dış çap, ağırlık, teslim boyu gibi doğrudan satır değerleri,
- `catalog_electrical`: Rdc, L, C ve referans ampacity değerleri,
- `reference_conditions`: toprak/hava sıcaklığı, gömülme, ısıl özdirenç, yük faktörü ve yerleşim notları.

Bunlar parametrik `cable_snapshot` içindeki koşullu geometriden ayrıdır. Böylece gerçek katalog kapasitansı, eşdeğer iç çaplardan hesaplanan geçici kapasitansla karıştırılmaz.

## 3. Konstrüksiyon yer tutucusu

Katalog satırlarının çoğu tam iç/ara çapları ve ekran tel geometrisini vermez. Arayüzün ve solver veri akışının çalışması için koşullu katman yığını oluşturulur; fakat:

- gerçek iletken çapı yerine eşdeğer daire çapı kullanıldığı belirtilir,
- iletken tel/segment yapısı `UNKNOWN_FROM_CATALOG` tutulur,
- ekran tel sayısı ve çapı sıfır/bilinmiyor bırakılır,
- iç çaplar `USER_ASSUMPTION` kaynağına bağlanır,
- doğrulama durumu `CONDITIONAL` kalır.

## 4. Gerilim sınıfı filtresi

Kablo etiketi `U0/U(Um)` biçiminden okunur. Sistem gerilimi sürekli işletme gerilimi `U` ile karşılaştırılır; yalnız `Um` değerine bakılarak uygundur kararı verilmez. Şebeke topraklama düzeni ve arıza süresi nihai gerilim sınıfı teyidinde ayrıca gereklidir.

## 5. Yük ve devre davranışı

Aday motoru proje sihirbazındaki hesapları kullanır:

- normal toplam akım,
- aktif devre başına normal akım,
- N-1 devre akımı,
- tasarım marjlı akım.

Katalog marjı, tasarım akımına göre hesaplanır. Paralel kablo/faz varyantları ayrı adaydır; tek bir katalog ampacity değeri sessizce devre sayısıyla çarpılmaz.

## 6. Referans ampacity seçimi

- `DIRECT_BURIED_TREFOIL` → toprakta trefoil değeri,
- `DIRECT_BURIED_FLAT` → toprakta flat değeri,
- `DUCT/HDD` → yalnız uyarılı toprak benchmarkı,
- eksik düzen → katalogdaki genel toprak değeri.

Duct/HDD için katalog toprak ampacity'si `PRELIMINARY_PASS` verse bile nihai hüküm üretmez; 2D kesit çözümü zorunludur.

## 7. Ön gerilim düşümü

Ön hesapta katalog Rdc/Rac ve L değerleri kullanılır. Sonuç:

- üç faz dengeli,
- sabit güç faktörlü,
- bölüm boyunca tek kesitli,
- yalnız ilk eleme

varsayımıdır. Dağıtılmış kapasitans, sıcaklık/akım iterasyonu, harmonikler, gerçek yük akışı ve farklı güzergâh bölümleri nihai çözümde değerlendirilir.

## 8. Sıralama

Motor en büyük kabloyu otomatik olarak birinci yapmaz. Puanlama:

- gerilim uyumsuzluğunu ağır cezalandırır,
- yetersiz ampacity'yi eler,
- pratik pozitif marja yaklaşımı tercih eder,
- gereksiz paralel kablo sayısını cezalandırır,
- koşullu konstrüksiyon ve düşük kaynak kalitesini işaretler,
- gerilim düşümünü ikincil ölçüt olarak kullanır.

Bu sıralama ekonomik optimizasyon değildir; fiyat, teslim süresi, tambur boyu ve inşaat maliyeti henüz amaç fonksiyonunda yoktur.

## 9. Projeye uygulama

Kullanıcı adayı seçtiğinde katalog ana kaydı projeye bağlı bırakılmaz. Tam veri kopyalanır ve yeni SHA-256 snapshot oluşturulur. Katalog paketi güncellense bile geçmiş proje değişmez. Kablo değişikliği IEC, termal, bonding, arıza ve SVL sonuçlarını `STALE` yapar.

## 10. Kabul kapısı

Bir adayın nihai tasarıma ilerlemesi için en az:

1. üretici konstrüksiyon çizimi,
2. gerçek ekran tel geometrisi veya metalik kılıf yapısı,
3. proje termal bölgeleri,
4. IEC 60287 ve 2D ampacity,
5. metalik kılıf/bonding kaybı,
6. faz iletkeni ve ekran kısa devre kontrolü,
7. arıza süresi/topraklama,
8. SVL gereksinimi,
9. geçici/acil yük profili

kontrol edilmelidir.

## 11. FAZ 6.8 — referans koşulu normalizasyonu

v0.16.9.4.27 ile eski “katalog ampacity ön elemesi” iki ayrı sayıya ayrılmıştır:

- `Iref arithmetic total = Iref_per_cable × target_parallel_count`: yalnız aritmetik görünüm,
- `normalized reference ampacity`: yalnız proje bölgesi ile katalog referans koşulu arasındaki bütün farklar kaynaklı faktörlerle kapatılmışsa üretilen benchmark.

Katalog kaydı `reference_conditions` içinde şu temel koşulları taşıyabilir:

- `soil_temperature_c`,
- `burial_depth_m`,
- `soil_thermal_resistivity_km_w`,
- `load_factor`,
- `cables_per_phase`,
- `arrangement`,
- `installation_method`,
- `correction_factors`.

Bir düzeltme faktörü örneği:

```json
{
  "factor_id": "K-RHO-12",
  "parameter": "soil_thermal_resistivity_km_w",
  "reference_value": 1.0,
  "target_value": 1.2,
  "factor": 0.94,
  "source_type": "LICENSED_STANDARD_USER_ENTRY",
  "source_reference": "Kullanıcının lisanslı standardındaki ilgili tablo/satır"
}
```

Açık kaynak paketi bu sayıları kendisi sağlamaz. Exact hedef değere kaynaklı faktör yoksa interpolasyon veya komşu satır tahmini yapılmaz.

### Paralel kablo

`Iref × N` çıplak çarpımı yalnız aritmetik toplamdır. Katalog koşulundaki `cables_per_phase` ile proje hedefi farklıysa `grouping_parallel` faktörü gerekir. Böylece önceki açıklamasız `%10` paralel derating yaklaşımı kaldırılmıştır.

### Yük faktörü

IEC 60287 steady-state karşılaştırması için katalog `load_factor=1.0` olmalıdır. Farklı load factor ile yayımlanmış bir rating skaler “düzeltme katsayısı” ile steady-state'e çevrilmez; IEC 60853 yük-zaman profili/çevrimsel rating kapsamına yönlendirilir.

### Fiziksel model kıyası

Fiziksel ampacity yalnız aynı katalog kaydının projeye immutable snapshot olarak atanmış aynı paralel varyantıyla eşleştirilir. Normalize katalog benchmark'ı ile fiziksel proje sonucu arasındaki fark sayısal ve yönlü raporlanır (`PHYSICAL_MODEL_LOWER/HIGHER`), fakat kaynaklandırılmamış sabit bir yüzde ile otomatik kabul/ret yapılmaz.
