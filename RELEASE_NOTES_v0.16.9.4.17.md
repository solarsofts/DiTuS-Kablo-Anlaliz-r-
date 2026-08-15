# DiTuS Kablo Analizör v0.16.9.4.17 — Katalog ve Parametrik Geometri FAZ 2

## Dağıtım kararı

- Açık kaynak paket içinde üretici katalog satırı veya katalog PDF'i taşınmaz.
- Katalog kütüphanesi, kullanıcı kayıt girişi, içe/dışa aktarma, aday karşılaştırma ve CAT/CALC/ASSUME provenance zinciri korunur.
- Üretici kataloglarına erişim yalnız ayrı kolaylık listesindeki katalog/indirme sayfaları üzerinden sağlanır; bağlantılar onay, temsilcilik veya işbirliği anlamına gelmez.

## Jenerik şablonlar

Paket yedi üretici-bağımsız, koşullu tohum şablonla gelir:

- 12/20 (24) kV: Al 150/25, Cu 240/25, Al 400/35
- 20,3/35 (40,5) kV: Al 240/25, Cu 400/35, Al 630/50
- 87/150 (170) kV: Al 1600, `HV-BOND-01`

Şablonlar katalog ürünü değildir. Yarı iletken, bant, sıkıştırma ve metalik ekran/sheath ayrıntıları ASSUME sınıfında tutulur; standart tabloların lisanslı kaynaklardan son kontrolü tamamlanana kadar kayıtlar `CONDITIONAL` kalır.

## Parametrik geometri

- Katman zinciri tek geometri otoritesidir.
- Dış çap artık girdi değil; iletken, yarı iletken, izolasyon, bant, ekran/sheath ve dış kılıf zincirinin çıktısıdır.
- Eski sabit 76/82/88 mm sınırları ve dış kılıfın kalan çapı doldurması kaldırıldı.
- Dış kılıf kalınlığı seçili profil formülünden üretilir; yedi şablonda 3,0–4,3 mm aralığındadır.
- Skaler `conductor_diameter_mm`, `t1_outer_diameter_mm`, `t2_outer_diameter_mm`, `sheath_mean_diameter_mm` ve `overall_diameter_mm` katmanlardan tek yönde senkronize edilir.
- Tohum, proje yükleme, katalog içe aktarma, katalog birleştirme, kayıt oluşturma, dışa aktarma ve sentetik demo yolları aynı zorunlu senkronizasyondan geçer.

## Malzeme ve doğrulama

- Bilinen XLPE, yarı iletken XLPE, PVC ve PE ısıl özdirençleri merkezi malzeme profilinden çözülür; paket içe alımındaki eski serbest değerler hesap girdisi olamaz.
- PVC profili 6,0 K·m/W, PE ve XLPE profilleri 3,5 K·m/W olarak merkezileştirildi.
- Kullanıcının girdiği yayımlanmış dış çap ile hesaplanan dış çap karşılaştırılır.
- Geometrik malzeme kütlesi ile kullanıcının girdiği yayımlanmış kg/km karşılaştırılır.
- Tolerans dışı sapmalar kaydı `CONDITIONAL` tutar ve çap/kütle sapmasını ayrı neden kodlarıyla yazar.

## Sentetik örnekler

- Eski üretici kayıtlarına bağlı bütün sentetik proje, seçim, karşılaştırma, uygulama, tedarik ve rapor çıktıları yeniden üretildi.
- Adaylar yalnız `Üretici A`, `Üretici B` ve `Üretici C` sentetik kayıtlarıdır.
- Yeni sentetik uygulama snapshot'ı: `SNAP-D9BEF1B8DCFC`.

## Korunan sınırlar

- Proje şeması `0.16.4` olarak kalır.
- IEC, bonding, termal, arıza, transient ve diğer çözüm denklemleri değiştirilmedi.
- FAZ 2 motor dizini değişiklikleri katalog/veri senkronizasyonu ile sınırlıdır: `application_database.py`, `cable_library.py`, `project.py` ve yeni `cable_template_generator.py`.
