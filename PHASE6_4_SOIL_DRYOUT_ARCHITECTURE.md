# FAZ 6.4 — Toprak Kuruması / Kritik İzoterm Üretim Zinciri

## Bağlayıcı karar

- Kuruma fiziksel girdileri `ThermalMaterialData.critical_dryout_temperature_c` ve `dry_state_thermal_resistivity_km_w` alanlarında malzeme bazında tutulur.
- İki alan birlikte tanımlanmalıdır; kuru durum ısıl özdirenci nemli durum değerinden büyük olmalıdır.
- Kuruma verisi yoksa mevcut nemli-zemin analitik/nodal yolları değişmeden kalır.
- Basit, tek izole ve doğrudan gömülü kabloda IEC iki-bölge kritik-izoterm bağıntısı analitik olarak uygulanabilir.
- Çok kablolu, karşılıklı ısıtmalı veya gerçek x-y geometride kritik izoterm üretim otoritesi nodal, malzeme-hücre bazlı doğrusal olmayan çözümdür. IEC basit iki-bölge bağıntısı bu geometriye körlemesine genişletilmez.
- Yeraltı su seviyesinde veya altında kalan hücreler kuru bölgeye geçirilemez.
- Kuruma iterasyonu yakınsamazsa nodal sonuç bağlayıcı kabul edilmez.
- Kuruma, fiziksel tasarım reddi ile model kapsamını ayırır: analitik çok-kablolu kuruma isteği `ANALYTIC_DRYOUT_REQUIRES_NODAL`, `physical_rejection=False` üretir.

## Analitik iki-bölge yolu

Basit izole kabloda:

1. Nemli-zemin T4 ile wet rating çözülür.
2. Kablo/zaman-bağımsız zemin arayüz sıcaklığı kritik izotermi aşmıyorsa wet rating korunur.
3. Kritik izoterm aşılırsa `rho_dry/rho_wet` oranını ve kritik sıcaklık artışını kullanan IEC iki-bölge formu ampacity ve tasarım sıcaklığına uygulanır.
4. Rac(T) sıcaklığa bağlı olduğundan tasarım sıcaklığı robust bracket/bisection çözümüyle bulunur.

## Nodal kritik-izoterm yolu

- Başlangıç alanı nemli malzeme ile çözülür.
- Her malzeme hücresi kendi kritik sıcaklığına göre değerlendirilir.
- Kritik izotermi aşan, kuruma açısından uygun hücreler `k=1/rho_dry` ile yeniden çözülür.
- Kuru maske monoton genişler; iletkenlik matrisi her iterasyonda yeniden kurulur/faktörlenir.
- Yakınsama; kuru hücre maskesinin kararlı hale gelmesi, nodal çözüm yakınsaması, enerji dengesi ve residual kapılarıyla birlikte değerlendirilir.
- Sonuçlar kuruyan hücre sayısı, uygun hücre sayısı, kuru fraksiyon, iterasyon sayısı ve malzeme kimlikleriyle izlenir.

## Üretim yöntemi

- `thermal_method=AUTO`, aktif kuruma verisi bulunmuyorsa `ANALYTIC`, bulunuyorsa `NODAL` seçer.
- Kuruma etkin projede açık `ANALYTIC` isteği model-kapsam hatasıdır.
- Başarılı nodal kritik-izoterm çalışma noktası, analitik IEC bölgesel yolun kapsam dışı olmasını toplam motor çökmesi haline getirmez; workflow `CONDITIONAL`/nodal-binding olarak izlenir.
- Analitik–nodal karşılaştırmada kuruma etkinse nodal kalite kapısı zorunludur; genel yöntem uyuşmazlığı kuralından ayrı `NODAL_DRYOUT_BINDING`/`QUALITY_PENDING` durumu kullanılır.

## İzlenebilirlik

Rapor ve trace içinde en az şu bilgiler görünür:

- kullanılan termal yöntem,
- kuruma malzemeleri,
- kritik sıcaklık ve nemli/kuru rho kaynağı,
- kuruyan/uygun hücre sayısı ve fraksiyon,
- kuruma iterasyon yakınsaması,
- yeraltı suyu engellemesi,
- nodal enerji dengesi ve residual kalite kapıları.

## Kapsam sınırı

- Bu faz IEC 60853 geçici/çevrimsel kuruma modelini uygulamaz.
- Nem transferi, histerezis, yeniden ıslanma ve zamana bağlı su hareketi çözülmez; model kararlı durum kritik-izoterm iki-bölge yaklaşımıdır.
- Malzeme kritik sıcaklığı/kuru rho değeri kaynaklandırılmamışsa sonuç veri güven durumunu yükseltmez.
