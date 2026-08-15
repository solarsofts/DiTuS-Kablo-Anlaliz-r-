# FAZ 6.3 — IEC 60287 Skin / Proximity Üretim Zinciri

## Bağlayıcı karar

- `skin_effect_factor` (`ys`) ve `proximity_effect_factor` (`yp`) artık bilinen iletken konstrüksiyonlarında üretim girdisi değildir.
- Üretim yolu `ks/kp -> xs/xp -> ys/yp -> Rac(T)` zincirini kullanır.
- `ks/kp`, açık ve izlenebilir çift verilmedikçe iletken malzemesi, şekli, tel/segment yapısı, izolasyon sistemi ve gerekli Milliken tel profiline göre çözülür.
- `COMPACT_ROUND`, yuvarlak kompakt çok telli iletken sınıfının geçerli eş adıdır.
- Cu Milliken için tel profili bilinmiyorsa katsayı tahmin edilmez. FAZ 6.9 uygulanabilirlik kapısı tamamlanana kadar bu durum açık `LEGACY_YS_YP_FALLBACK` iziyle koşullu çalışabilir; sessiz fallback yasaktır.
- Proximity faktörü gerçek/çözülmüş `phase_spacing_m` ile hesaplanır. Geometri bulunmayan düşük seviye legacy çağrılar sabit katsayı yolunu yalnız uyumluluk fallback'i olarak kullanabilir.
- 20 °C altı fiziksel Rac hesabı FAZ 3.1 sıcaklık sözleşmesine uygundur; yapay 20 °C alt sınırı yoktur.

## Üretim kapsamı

Aşağıdaki yollar geometri mevcut olduğunda fiziksel Rac kullanır:

- IEC 60287 bölüm çözücüsü,
- primitive bonding ağı,
- global çok-iletken EM ağı,
- çok-iletken analitik/nodal termal çözüm,
- legacy nodal çözüm,
- transient termal çözüm.

Üretim kapalı çevrimi sıcaklık değiştikçe Rac'ı yeniden çözer.

## IEC bölüm çözümünde sıcaklık

`ys/yp` sıcaklıkla değiştiği için eski sabit-katsayılı kapalı form tasarım sıcaklığı hesabı artık üretim otoritesi değildir. Tasarım sıcaklığı şu sabit noktanın robust bracketing/bisection çözümüyle bulunur:

`T = Tamb + ΔTdielectric + I² * Rac(T) * Rthermal_chain`

Termal kararsızlık kapısı korunur.

## İzlenebilirlik

`thermal_trace` içinde Rdc20 kaynağı, α20 kaynağı, `ks/kp`, `xs/xp`, `ys/yp`, faz aralığı ve Rac kaynağı ayrı yazılır. Legacy fallback kullanılırsa nihai tasarım için konstrüksiyon kaynağı doğrulama notu üretilir.

## Kapsam sınırı

Bu faz tam N-kablo arbitrary-x/y proximity integralini uygulamaz. Çok-iletken üretim yolunda IEC tek-kablo konstrüksiyon proximity terimi çözülmüş güzergâh faz aralığına dayanır. Arbitrary x-y genişletmesi ayrı model doğrulaması gerektirir.
