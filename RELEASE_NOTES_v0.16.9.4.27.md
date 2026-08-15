# DiTuS Kablo Analizör v0.16.9.4.27

## FAZ 6.8 — Katalog referans ampacity doğrulama zinciri

Bu sürüm v0.16.9.4.26 FAZ 6.5 tabanı üzerinde katalog referans akımını yayımlanmış referans koşullarına bağlar ve proje koşullarına normalizasyonu fail-closed hale getirir.

- Katalog `Iref`, tek başına proje ampacity'si değildir; referans toprak sıcaklığı, gömme derinliği, toprak ısıl özdirenci, dizilim, kurulum tipi, yük faktörü ve referans paralel kablo sayısıyla birlikte değerlendirilir.
- Referans koşulu hedef koşulla aynıysa ilgili düzeltme katsayısı `1.0` kabul edilir; farklıysa açık ve izlenebilir bir düzeltme faktörü zorunludur.
- Paket lisanslı IEC/national/manufacturer düzeltme tablolarının sayısal içeriklerini gömmez, interpolasyon veya tahmin yapmaz.
- `Iref × paralel kablo sayısı` yalnız aritmetik toplamdır; grouping/parallel faktörü yoksa normalize edilmiş rating üretilmez.
- Route-bazlı normalizasyon yapılır ve bütün bölgeler tamamlandığında en düşük normalize `Iref` governing referans olur.
- Kaynak doğrulanmış faktörler ile mühendislik varsayımı faktörleri ayrılır; varsayım zinciri `NORMALIZED_CONDITIONAL` kalır.
- Katalog yük faktörü `1.0` değilse steady-state skaler düzeltme uygulanmaz; `CYCLIC_REFERENCE_REQUIRES_IEC60853` üretilir.
- Fiziksel IEC/nodal ampacity ile katalog referansı yalnız aynı uygulanmış katalog kaydı ve aynı paralel sayısı için yönlü olarak karşılaştırılır; keyfi yüzde toleransla PASS/FAIL verilmez.
- Eski ilk-tasarım `parallel_derating=0.90` varsayımı kaldırılmıştır. Çoklu paralelde faktör yoksa çıktı açıkça gruplama doğrulaması gerektirir.
- Kablo kütüphanesine `Iref / Koşullar` editörü ve karşılaştırma ekranına aritmetik/normalize referans ayrımı eklenmiştir.
- Sentetik kataloglarda normatif düzeltme faktörü uydurulmaz; normal adaylar bu nedenle koşullar farklıysa `REFERENCE_NORMALIZATION_REQUIRED` kalır.
- Proje şeması `0.16.4` olarak korunmuştur.

Nihai hesap otoritesi FAZ 4.2'de tanımlanan fiziksel IEC/nodal yöntem otoritesi olmaya devam eder; katalog zinciri doğrulama ve karşılaştırma kanıtıdır.
