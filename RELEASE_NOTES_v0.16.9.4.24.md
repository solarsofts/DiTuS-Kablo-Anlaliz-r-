# DiTuS Kablo Analizör v0.16.9.4.24 — FAZ 6.3 IEC Skin / Proximity

- IEC 60287 AC direnç üretim yolu sabit `ys=0.025`, `yp=0.015` varsayımlarından konstrüksiyon tabanlı `ks/kp -> ys/yp` çözümüne geçirildi.
- Al/Cu solid, round/compacted stranded ve tanımlı Milliken profilleri için mevcut IEC konstrüksiyon resolver'ı üretim zincirine taşındı.
- `COMPACT_ROUND` konstrüksiyon eş adı desteklendi.
- Cu Milliken UNKNOWN profili tahmin edilmez; legacy uyumluluk fallback'i açıkça izlenir.
- Tasarım çalışma sıcaklığı, sıcaklığa bağlı `ys/yp` nedeniyle doğrusal kapalı form yerine Rac(T) sabit noktasından çözülür.
- IEC, primitive bonding, nodal, transient ve çok-kablolu termal Rac çağrıları geometri mevcutken faz aralığını fiziksel çözücüye verir.
- FAZ 3.1 ile uyumlu olarak fiziksel Rac 20 °C altındaki sıcaklıklarda da çalışır.
- Sentetik 20 km çıktı zinciri yeniden üretildi. Yeni proje kablosu snapshot'ı `SNAP-D5AB88B00AF0`.
- Sentetik DESIGN üretim çalışma noktası yeni konstrüksiyon Rac ile yaklaşık `144.735703 °C` maksimum iletken sıcaklığı üretir ve `UYGUN_DEGIL` kalır.
- 1200 mm² Cu Milliken `BARE_BIDIRECTIONAL` testinde skin faktörü `ys > 0.10` olarak doğrulanır; böylece büyük kesitte eski sabit `0.025` iyimserliği regresyonla yakalanır.
- Proje şeması `0.16.4` değişmedi.
