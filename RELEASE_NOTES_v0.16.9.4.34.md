# DiTuS Kablo Analizör v0.16.9.4.34 — P0 Sheath Loss Completeness Closure

- Primitive/global bonding ağındaki boyuna metalik kılıf I²R oranı `network_sheath_loss_ratio` olarak ayrıldı; toplam IEC λ1 anlamında sunulması engellendi.
- IEC rating için `λ1 rating = network longitudinal + λ1″ eddy` provenance zinciri kuruldu.
- IEC 60287-1-1 2.3.6.1 Trefoil ve desteklenen Flat tekli-devre geometrileri için otomatik λ1″ hesabı eklendi.
- `m <= 0.1` durumunda λ0 korunur; yalnız Δ1/Δ2 terimleri düşürülür.
- Büyük dilimli Milliken kolunda 2.3.5 `F` faktörü λ1″ ile birlikte uygulanır.
- Explicit Note 3 ekran konstrüksiyonu için eddy kaybının ihmal edilebilirliği kaynaklandırılmış FULL karar olarak taşınır; wire screen tek başına Note 3 kabul edilmez.
- Solid both-end, non-Milliken tek damarlı kol IEC 2.3 kapsamına göre ek λ1″ istemeden FULL kalır.
- CUSTOM ve paralel/çok-devre kesitlerde 2.3 kapalı form otomatik genişletilmez; doğrulanmış harici λ1″ yoksa IEC ampacity fail-closed bloke edilir.
- Harici λ1″ için referans koşulları ve stale kapıları eklendi.
- Al büyük kılıf Note 2 evidence kodu eklendi.
- UI/raporda λ1′ network, λ1″ eddy, λ1 rating ve authority/provenance ayrımı görünür hale getirildi.
- Sentetik 20 km proje çok-devreli olduğundan otomatik kapalı-form λ1″ kapsamı dışındadır; çalışma noktası BLOCKED authority ile raporlanır, ampacity dış döngüsü harici doğrulanmış λ1″ olmadan üretim sonucu vermez.
- Proje şeması 0.16.4 olarak korunmuştur.
