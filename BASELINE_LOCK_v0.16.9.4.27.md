# Baseline Lock — v0.16.9.4.27

Bu sürüm FAZ 6.8 katalog referans ampacity koşul ve düzeltme zincirini üretime taşır.

- Proje şeması: `0.16.4`
- Hesap/model dosyaları bu sürümün motor baseline'ıyla hash-kilitlidir.
- Hesap/model yayın hash kümesi: `ENGINE_BASELINE_v0.16.9.4.27.sha256`
- Katalog `Iref` ancak referans koşullarıyla birlikte anlamlıdır; koşul farkında açık kaynaklı/izlenebilir faktör olmadan normalize rating üretilmez.
- Paralel kablo aritmetik toplamı fiziksel grouping rating değildir; eski sabit `%0.90` derating kaldırılmıştır.
- IEC 60287 steady-state referansı için `load_factor=1.0` beklenir; cyclic referanslar IEC 60853 kapsamına yönlendirilir.
- Katalog-fiziksel model karşılaştırması yalnız aynı uygulanmış katalog kaydı ve aynı paralel sayısı için yönlü kanıt üretir.
- FAZ 6.5 yük faktörü, FAZ 6.4 kuruma, FAZ 6.3 konstrüksiyon tabanlı Rac, FAZ 6.1/6.2 kayıp vektörü, FAZ 4 geometri/yöntem otoritesi ve FAZ 5 procurement sözleşmeleri korunur.
