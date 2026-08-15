# FAZ 8.0 — Arayüz Kabuğu Kapanışı

Sürüm: 0.16.9.4.37

Bu faz yeni fizik eklemez. Mevcut motorların kullanıcıya nasıl sunulduğunu
düzeltir: pencerelerin dağılması, akışın yön göstermemesi, ağacın yarısının
sessiz kalması ve lisanslı katsayı tablosunun pakete gömülü olması.

## 1. Tek boyut otoritesi — `ucd.ui.window_layout`

**Sorun.** Boyut kararı iki yerdeydi. Her diyalog kurucusunda mutlak
`resize(1540, 900)` vardı; ana pencere ayrı bir yardımcıyla *bazı* diyalogları
ekrana sığdırıyordu. Sonuçları:

- diyalog içinden açılan alt diyaloglar sığdırma yolundan hiç geçmiyordu,
- 1366×768 gibi yaygın ekranlarda tercih edilen boyutlar ekranı aşıyordu,
- alt yerleşimlerin dayattığı minimumlar sığdırmayı geçersiz kılabiliyordu.

**Karar.** Pencere artık piksel değil **yoğunluk** bildirir:
`COMPACT` / `NORMAL` / `WIDE` / `FULL`. Gerçek geometri aktif ekranın
kullanılabilir alanından çözülür. Taban değerler vardır ama ekran her zaman
kazanır; küçük ekranda okunmaz pencere, ekran dışına taşan pencereden iyidir.

Ana penceredeki `_fit_dialog_to_available_screen` yalnız ince bir
sarmalayıcıdır; geometri matematiği taşımaz. İç içe açılan diyaloglar da aynı
yoldan geçer. Regresyon testi hiçbir UI modülünün mutlak boyut sabitlemesine
izin vermez.

## 2. Aşama konağı — `ucd.ui.stage_host`

**Sorun.** "Tasarım akışını başlat" onayından sonra aşamalar ard arda bağımsız
üst düzey pencereler olarak açılıyordu. Asıl sorun pencere sayısı değil, hiçbir
pencerenin akışta *nerede* olunduğunu taşımamasıydı.

**Karar.** Aşama içeriğinin etrafına sabit bir çerçeve konur:

- üstte adım numarası, başlık, durum rozeti ve sonraki işlem,
- ortada mevcut çalışma alanı widget'ı (yeniden yazılmadı, olduğu gibi kullanılır),
- altta eksik girdiler ve gezinme: önceki / önerilen / sonraki / akıştan çık.

Üst düzey pencere sayısı düşer, iterasyon yön gösterici olur.

## 3. Ağaç durum kaplaması

**Sorun.** Renk ve eksik listesi yalnız "Proje Tasarım Akışı" dalında vardı.
Nesne, sonuç ve çıktı dallarında ne renk ne açıklama bulunuyordu. Tooltip düz
metindi ve uzun eksik listelerinde tek blok halinde taşıyordu.

**Karar.** Aynı veri modeli (`missing_inputs` / `blocking_reasons` / `notes`)
tüm dallara bağlandı. Tooltip genişliği sınırlı zengin metne çevrildi. Grup
düğümü altındaki en kötü çocuk durumunu rozetler: `■` bloke/veri eksik,
`▲` koşullu, `○` başlanmadı. Böylece ağacı açmadan da nerede sorun olduğu
görünür.

## 4. Standart katsayıları ön tanım ekranı

**Sorun.** Lisanslı standart tablolarının pakete gömülü olması yayın riski
taşıyordu; kaldırıldığında ise kullanıcı değeri nereden bulacağını bilemezdi.

**Karar.** Ayarlar altında tek ekran. Dört sekme: İletken (ks/kp), Zemin ve
Ortam, Yalıtkan, Kılıf/Ekran. Her alanın üç sözleşmesi vardır:

1. Değerin **hangi standardın hangi maddesinden** bulunacağı alanın altında
   yazar (ör. `IEC 60287-1-1 Çizelge 2`, `IEC 60287-3-1 md. 4.2.3 Çizelge 2`).
2. Her değer bir **provenance** taşır: üretici veri sayfası, kendi standart
   nüshası, ölçülen Rac/Rdc'den geri hesap, kurum onaylı paket. Değer girilmiş
   ama kaynak seçilmemişse alan tamamlanmış sayılmaz.
3. Eksik değer **atlanamaz**. Hesap kapısı fail-closed davranır ve motor
   çalıştırılmadan önce durur.

Eksik değerde kullanıcı bir hata ekranı görmez; doğrudan ilgili ayar sekmesini
açan bir kart görür. `focus_on()` odaklanacak alanı seçer, kullanıcı sekme
aramaz.

Paket içe/dışa aktarma vardır: bir kurum kendi onaylı katsayı paketini bir kez
hazırlayıp mühendislerine dağıtabilir.

DiTuS hiçbir lisanslı tabloyu çoğaltmaz; yalnız madde kimliğini gösterir. Bu,
`SOURCES.md` içinde üretici katalog verisi için kurulmuş ilkenin standart
katsayılarına uygulanmış halidir.

## 5. Katsayı kademelendirmesi — lisanslı içeriğin paketten çıkarılması

Gömülü ks/kp değerleri riskine göre üç kademeye ayrıldı:

**Kademe 1 — kalır.** `ks = kp = 1`. Bu bir veri değil, düzeltme yokluğudur.
Kaynak etiketi `NO_CONSTRUCTION_CORRECTION`.  Yuvarlak masif ve Cu yuvarlak
çok telli ekstrüde bu gruptadır; XLPE kabloların büyük çoğunluğunu kapsar.

**Kademe 2 — kalır, atıf düzeltilir.** `kp = 0,8` durumları.  Bu değerler IEC
60287'nin icadı değildir; deri ve yakınlık düzeltmelerinin kökeni Neher-McGrath
soyuna dayanır ve onlarca bağımsız kaynakta yayımlanmıştır.  Kaynak etiketi
`IEC_CONSTRUCTION_TABLE` yerine `ESTABLISHED_ENGINEERING_VALUE` oldu.

**Kademe 3 — çıkarıldı.** Dilimli Milliken katsayı çiftleri.  Modern alt
sınıflandırma (yalıtılmış tel / çıplak tek yön / çıplak çift yön) doğrudan
IEC-CIGRE çalışmasının ürünü ve tablonun ayırt edici kısmıdır.  Motor artık
`USER_DEFINED_COEFFICIENT_REQUIRED` döndürür, sayı üretmez ve değerin nereden
bulunacağını üç yolla söyler: IEC 60287-1-1 Çizelge 2 dilimli Milliken satırı,
üretici veri sayfası, veya bilinen frekans/sıcaklıkta ölçülen Rac/Rdc oranından
geri hesap.

Kullanıcı doğrulanmış çifti girdiğinde `EXPLICIT_TRACEABLE_INPUT` yoluyla motor
aynen çalışır; kayıp yalnız gömülü tablodur, yetenek değil.

Bu, `SOURCES.md` içinde üretici katalog verisi için kurulmuş ilkenin standart
katsayılarına uygulanmış halidir: **DiTuS motor ve provenance sağlar, lisanslı
veriyi kullanıcı getirir.**

## Test

`tests/test_phase8_0_ui_shell_closure.py` — 15 test, dört sözleşmeyi kilitler.
Tam küme: 519 PASS.
