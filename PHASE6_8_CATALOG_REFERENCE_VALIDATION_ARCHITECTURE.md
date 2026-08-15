# DiTuS Kablo Analizör — FAZ 6.8 Katalog Referans Ampacity Doğrulama Mimarisi

Sürüm hedefi: **v0.16.9.4.27**  
Taban: **v0.16.9.4.26**  
Proje şeması: **0.16.4 (değişmedi)**

## 1. Amaç

Katalog akım taşıma kapasitesini, yayımlandığı koşullardan koparılarak proje ampacity'si gibi kullanılmaktan çıkarmak; referans koşullarını proje güzergâh koşullarına izlenebilir biçimde dönüştürmek ve bu benchmark'ı gerçek IEC/nodal fiziksel proje sonucuyla ayrı bir kanıt katmanı olarak karşılaştırmak.

## 2. Otorite hiyerarşisi

1. Nihai proje rating otoritesi: FAZ 4.2 yöntem otoritesi altındaki fiziksel IEC/nodal proje hesabı.
2. Kaynaklı normalize katalog rating'i: bağımsız validation benchmark'ı.
3. Ham katalog Iref: yalnız yayımlandığı referans koşulun kanıtı.
4. `Iref × parallel_count`: yalnız aritmetik görünüm; rating değildir.

Katalog karşılaştırması hiçbir durumda fiziksel proje hesabını geçersiz kılmaz veya onun yerine geçmez.

## 3. Referans koşulları

`CableCatalogRecord.reference_conditions` mevcut dict alanı korunur; proje schema değişmez. Desteklenen anahtarlar:

- `soil_temperature_c`
- `burial_depth_m`
- `soil_thermal_resistivity_km_w`
- `load_factor`
- `cables_per_phase`
- `arrangement`
- `installation_method`
- `correction_factors`

Ampacity'nin arrangement bilgisi mümkün olduğunda seçilen katalog alanından (`ampacity_ground_trefoil_a`, `ampacity_ground_flat_a`) türetilir; tek global arrangement notu bu daha kuvvetli kanıtı ezmez.

## 4. Düzeltme faktörü sözleşmesi

Her faktör en az şu alanları taşır:

- `factor_id`
- `parameter`
- `reference_value`
- `target_value`
- `factor`
- `source_type`
- `source_reference`
- opsiyonel `source_id`

Desteklenen parametreler:

- `soil_temperature_c`
- `burial_depth_m`
- `soil_thermal_resistivity_km_w`
- `arrangement`
- `installation_method`
- `grouping_parallel`

Paket lisanslı IEC/national/manufacturer tablo satırı taşımaz. Referans ve hedef aynıysa `k=1`. Farklıysa exact eşleşen faktör gerekir; interpolasyon, extrapolasyon veya komşu satır tahmini yapılmaz.

Kaynak sınıfları:

- doğrulanmış: `STANDARD_TABLE`, `NATIONAL_TABLE`, `MANUFACTURER`, `MANUFACTURER_VERIFIED`, `TEST_VERIFIED`, `USER_VERIFIED`, `LICENSED_STANDARD_USER_ENTRY` + kaynak referansı,
- koşullu: `ASSUMPTION`, `ENGINEERING_ASSUMPTION`, `SYNTHETIC_DEMO`,
- diğer/eksik: unverified.

## 5. Güzergâh-bazlı normalizasyon

Her `RouteSection` ayrı target condition üretir. Her bölüm için:

`I_adjusted_region = Iref_per_cable × N_target × Π(k_i)`

Ancak bu denklem yalnız bütün değişen koşullar için faktör bulunduğunda geçerlidir. Eksik parametre varsa bölüm `REFERENCE_ONLY_INCOMPLETE` olur ve adjusted rating üretilmez.

Bütün route bölümleri complete ise katalog benchmark'ı:

`I_adjusted_governing = min(I_adjusted_region)`

olarak raporlanır.

## 6. Paralel kablo / grouping

Referans `cables_per_phase` ile hedef parallel count farklıysa `grouping_parallel` faktörü zorunludur. Çıplak `Iref × N` yalnız `arithmetic_total_ampacity_a` alanında tutulur.

İlk tasarım jenerik motorundaki sabit `parallel_derating=0.90` kaldırılır. Çoklu kablo/faz ön tahmini aritmetik üst sınırdır ve `GRUPLAMA_DOGRULAMASI_GEREKLI` durumundadır.

## 7. Load factor

IEC 60287 steady-state benchmark'ı için reference `load_factor=1.0` gerekir. `load_factor != 1.0` ise:

`CYCLIC_REFERENCE_REQUIRES_IEC60853`

üretilir; skaler düzeltme uygulanmaz. FAZ 6.5 yük profili/LF/μ sözleşmesi korunur.

## 8. Normalizasyon durumları

- `REFERENCE_MISSING`
- `REFERENCE_ONLY_INCOMPLETE`
- `NORMALIZED_SOURCE_VERIFIED`
- `NORMALIZED_CONDITIONAL`
- `CYCLIC_REFERENCE_REQUIRES_IEC60853`

Aday screening durumu ayrıca:

- `FAIL`
- `REFERENCE_ONLY`
- `NORMALIZED_FAIL`
- `NORMALIZED_PASS`

olabilir. `NORMALIZED_FAIL`, yalnız katalog benchmark'ının tasarım akımının altında olduğunu söyler; fiziksel tasarım hükmü değildir.

## 9. Fiziksel model karşılaştırması

Fiziksel rating yalnız şu durumda katalog adayına bağlanır:

- `record_id` projeye atanmış katalog kaydıyla aynı,
- `parallel_cables_per_phase` aynı,
- normalize katalog benchmark'ı complete.

Raporlanan metrikler:

- fiziksel ampacity,
- `physical - normalized_catalog` A,
- aynı fark %,
- `ALIGNED`, `PHYSICAL_MODEL_LOWER`, `PHYSICAL_MODEL_HIGHER`.

Bu sürüm fark için keyfi bir kabul yüzdesi tanımlamaz. Nihai hüküm FAZ 4.2 yöntem otoritesindedir.

## 10. UI

Kablo veri tabanında `Iref / Koşullar` düzenleyicisi:

- trefoil/flat Iref,
- referans toprak sıcaklığı,
- referans derinlik,
- referans ρth,
- load factor,
- kablo/faz,
- arrangement,
- installation method,
- traceable correction-factor JSON

girdilerini yönetir.

Katalog aday ve karşılaştırma ekranları ham aritmetik Iref ile normalize Iref'i ayrı sütunlarda gösterir. Fiziksel model sonucu varsa aynı uygulanmış adayda yönlü kıyas eklenir.

## 11. Fail-closed kuralları

- Eksik referans koşulu → adjusted rating yok.
- Farklı koşul + faktör yok → adjusted rating yok.
- Paralel sayısı farklı + grouping faktörü yok → adjusted rating yok.
- LF != 1 → IEC 60287 normalizasyonu yok.
- Kaynaksız/varsayımsal faktör → hesaplanabilir ama `NORMALIZED_CONDITIONAL`.
- Duct/HDD için direct-buried katalog rating'i yalnız installation-method faktörü varsa normalize olabilir.
- Katalog benchmark'ı fiziksel proje rating'i olarak raporlanamaz.

## 12. Veri lisansı ve açık kaynak sınırı

Bu mimari lisanslı standardın sayısal tablosunu dağıtmaz. Kullanıcı sahip olduğu standardın/table datasının ilgili satırını kendi yerel veri tabanına kaynak referansıyla girebilir. Açık kaynak repo yalnız schema, doğrulama, provenance ve hesap zincirini içerir.
