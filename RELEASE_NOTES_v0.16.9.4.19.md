# DiTuS Kablo Analizör v0.16.9.4.19 — FAZ 3.2 Yerleşim Kapsamı

## VERTICAL

- Analitik termal, bonding ve primitive ağ için VERTICAL faz koordinatları eklendi.
- `burial_depth_m` en sığ kablo ekseni, `phase_spacing_m` komşu eksen aralığı olarak tek anlamda kullanılır.
- Doğrudan gömülü VERTICAL yerleşimde faz aralığı kablo dış çapından küçükse fiziksel çakışma kapısı çalışır.
- TREFOIL, FLAT ve VERTICAL aynı ortak faz-slot geometri üreticisini kullanır.

## Kurulum tipi / formasyon ayrımı

- DUCT_BANK faz formasyonu olmaktan çıkarıldı; yalnız kurulum tipidir.
- CUSTOM açık x-y geometrisidir ve analitik image-method motoru explicit koordinatlarla çalışabilir.
- `installation_coupling` içindeki bilinmeyen yerleşimi sessizce Flat'e çeviren davranış kaldırıldı.
- Legacy DUCT_BANK etiketi gerçek x-y varsa CUSTOM olarak korunur.

## Analitik model kapsamı

- `AUTO_IMAGE` ve `AUTO_MIXED_ZONE` yalnız `DIRECT_BURIED` için geçerlidir.
- DUCT_BANK, HDD, CONCRETE_TROUGH ve TUNNEL nodal çözüm veya kaynaklandırılmış manuel T4 ister.
- Desteklenmeyen kombinasyon `ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL` ile bölüm-özgü hata olur.
- Hata `physical_rejection=False` taşır; tek başına `UYGUN_DEGIL` oluşturmaz.
- Üretim geometri senkronizasyonu kullanıcı termal modunu artık sessizce MANUAL'a dönüştürmez.

## Bonding ve Single

- Bonding VERTICAL fallback geometrisi desteklenir.
- SINGLE bonding, açık dönüş yolu geometrisi olmadan `BONDING_SINGLE_REQUIRES_RETURN_PATH_GEOMETRY` üretir.

## UI

- Formasyon listesi TREFOIL / FLAT / VERTICAL / CUSTOM olarak ayrıştırıldı.
- Duct satır/sütun alanları kurulum tipinden, faz aralığı alanı formasyondan yönetilir.
- Özel kurulum tipleri için nodal veya manuel T4 gerekliliği erken gösterilir.

## Sentetik örnekler

- En sığ eksen derinliği sözleşmesine göre kritik doğrudan gömülü sentetik kesitin hendek derinliği düzeltildi.
- Sentetik proje, katalog, uygulama, tedarik ve rapor çıktıları yeniden üretildi.
- Proje şeması `0.16.4` olarak korunur.
