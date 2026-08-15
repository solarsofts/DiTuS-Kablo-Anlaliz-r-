# DiTuS Kablo Analizör v0.16.9.4.35 — FAZ 8.0 Arayüz Kabuğu Kapanışı

- Pencere boyutu kararı tek otoriteye alındı (`ucd.ui.window_layout`). Diyaloglar
  artık piksel değil yoğunluk sınıfı bildirir; geometri aktif ekranın
  kullanılabilir alanından çözülür. Diyalog içinden açılan alt diyaloglar da bu
  yoldan geçer.
- Aşamalar ard arda bağımsız pencere açmaz. Yeni `StageHostFrame` sabit bir akış
  çerçevesi taşır: adım numarası ve durum, eksik girdiler, önceki/önerilen/sonraki
  gezinme ve akıştan çıkış.
- Sağ ağaçtaki renk ve eksik açıklaması tüm dallara yayıldı; tooltip genişliği
  sınırlı zengin metne çevrildi; grup düğümleri en kötü çocuk durumunu rozetler.
- Ayarlar altına "Standart Katsayıları ve Varsayılanlar" ön tanım ekranı eklendi.
  Her alan hangi standardın hangi maddesinden bulunacağını gösterir, provenance
  taşır ve paket olarak dışa aktarılabilir.
- Eksik standart katsayısı hesap motorunu fail-closed durdurur; kullanıcı hata
  ekranı yerine doğrudan ilgili ayar sekmesine yönlendirilir.
- Dilimli Milliken ks/kp katsayı çiftleri paketten çıkarıldı. Bu değerler
  IEC/CIGRE alt sınıflandırmasının ürünü ve lisanslı tablonun ayırt edici
  kısmıdır; motor artık `USER_DEFINED_COEFFICIENT_REQUIRED` ile fail-closed
  durur ve değerin nereden bulunacağını söyler.
- `ks = kp = 1` durumları `NO_CONSTRUCTION_CORRECTION` olarak etiketlendi; bu
  bir tablo verisi değil, düzeltme yokluğudur.
- Yaygın yayımlanmış yakınlık düzeltmesi (`kp = 0,8`) pakette kalır ama kaynağı
  `ESTABLISHED_ENGINEERING_VALUE` olarak işaretlenir; IEC tablosundan alınmış
  gibi sunulmaz.
- Proje şeması değişmedi: 0.16.4.
