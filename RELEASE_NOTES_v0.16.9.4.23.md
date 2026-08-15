# DiTuS Kablo Analizör v0.16.9.4.23 — FAZ 6.1/6.2 Üretim Elektro-Termal Bağlaşımı

Bu sürüm v0.16.9.4.22 FAZ 5 tabanı üzerinde senaryo-bazlı akım/enerjilenme vektörünü, global bonding kayıplarını ve gerçek x-y termal matrisi kapalı çevrimde birleştirir.

## Başlıca değişiklikler

- NORMAL, DESIGN ve devre-bazlı N-1 çalışma noktaları eklendi.
- Fiziksel varlık, enerjilenme ve RMS akım birbirinden ayrıldı.
- `load_factor` kararlı durum RMS akımına uygulanmıyor.
- Global N-core/N-sheath ağı fiziksel kablo akım override'larını üretim kısıtı olarak kullanıyor.
- Kablo kayıpları `Rth × q` vektörüyle termal alana aktarılıyor.
- Devre dışı kablolar geometriden silinmiyor; elektriksel ve dielektrik kayıpları sıfırlanıyor.
- Enerjili sıfır-akım kabloda dielektrik kayıp korunuyor ve λ1 uygulanabilir değil.
- λ1 fiziksel kılıf/iletken kaybından türetiliyor; proje kablosuna yazılmıyor.
- Hedef-devre ve ortak ölçekli kapalı-çevrim ampacity fonksiyonları eklendi.
- Analitik ve nodal yöntemlerin aynı dondurulmuş kayıp vektörüyle doğrulanması eklendi.
- UI ve headless rapor/demolar aynı üretim orkestratörüne bağlandı.
- Proje raporuna senaryo akım/enerjilenme, sıcaklık, λ1 ve kayıp fingerprint tablosu eklendi.

## Kapsam dışı

Skin/proximity formülleri, toprak kuruması, çevrimsel yük faktörü, çok-devre kılıf indüksiyonu ve kümülatif standing-voltage profili sonraki FAZ 6 alt başlıklarındadır.

- Proje şeması: `0.16.4`
- Üretim snapshot: `SNAP-2938BDC33EFE`
