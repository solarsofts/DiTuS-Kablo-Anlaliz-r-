# DiTuS Kablo Analizör v0.16.9 — Kablo-Kanal Düzeni Teknik Notları

## 1. Amaç

Bu sürüm, v0.16.8 kilitli hesap mimarisini değiştirmeden her termal güzergâh section'ı için fiziksel kablo yerleşimi ile hendek/kanal yapısını aynı modelde tanımlar.

Ekran adı: **Kablo-Kanal Düzeni**.

Her kesit aşağıdaki bileşenleri birlikte taşır:

- kurulum tipi,
- fiziksel kabloların x–derinlik koordinatları,
- hendek/kanal ölçüleri,
- yataklama, termal backfill, seçilmiş dolgu ve yüzey tabakaları,
- duct bank, beton trough, HDD veya tünel boyutları,
- koruma plakası,
- malzeme kimlikleri,
- harici doğrusal ısı kaynakları,
- bağlı termal bölge kimlikleri.

## 2. İnteraktif davranış

Kanvas üzerindeki sarı tutamaçlarla şu değerler doğrudan değiştirilebilir:

- hendek genişliği,
- hendek derinliği,
- yataklama kalınlığı,
- termal backfill yüksekliği,
- koruma plakası derinliği.

Kanvas ve sayısal alanlar çift yönlü senkron çalışır. Kablolar ayrıca sürüklenerek x–derinlik koordinatları değiştirilebilir.

Sağ panel kaydırılabilir hale getirilmiştir; küçük ekranlarda geometri ve malzeme alanları tabloları taşırmaz.

## 3. Kurulum tipleri

Teknik enum korunur, yanında küçük ve italik Türkçe açıklama gösterilir:

- `DIRECT_BURIED` — *doğrudan gömülü*
- `DUCT_BANK` — *boru / kanal bankası*
- `CONCRETE_TROUGH` — *beton kablo kanalı*
- `HDD` — *yatay yönlendirilmiş sondaj*
- `TUNNEL` — *kablo tüneli*

Kurulum tipi değiştiğinde kanvastaki parametrik yapı değişir. Mevcut kablo koordinatları sessizce silinmez.

## 4. Veri modeli

Yeni eklemeli model: `CableChannelGeometryData`.

Başlıca alanlar:

- `center_x_m`
- `trench_width_m`, `trench_depth_m`
- `bedding_thickness_m`
- `thermal_backfill_height_m`
- `selected_fill_thickness_m`
- `surface_layer_thickness_m`
- koruma plakası ölçüleri
- duct bank ölçüleri
- trough iç ölçüleri ve duvar kalınlığı
- HDD delgi çapı
- tünel ölçüleri
- her bölge için termal malzeme kimliği
- `source_reference`

Proje şeması **0.16.4 olarak korunmuştur**. Yeni alanlar eski projelerde geriye uyumlu varsayılanlarla oluşturulur.

## 5. Legacy koruması

Eski projeler açıldığında otomatik üretilen kesitlerin `source_reference` değeri legacy statüsündedir. Kullanıcı kesiti düzenleyene veya kurulum tipine göre yeniden kurana kadar bu geometri fiziksel gölge termal motorun eski termal profilini değiştirmez.

Böylece:

- eski üretim IEC sonucu değişmez,
- eski nodal üretim sonucu değişmez,
- eski gölge karşılaştırma sessizce yeni hendeğe geçirilmez.

Kullanıcı geometriyi değiştirdiğinde kaynak `USER_INTERACTIVE_GEOMETRY` olur ve yeni kesit gölge 2D termal modele aktarılır.

## 6. Gölge termal bağlantı

Kullanıcı tarafından kabul edilen kesit için aşağıdakiler `multiconductor_thermal` gölge motoruna aktarılır:

- gerçek hendek merkezi, genişliği ve derinliği,
- gerçek kablo x–derinlik koordinatları,
- gerçek katman kalınlıkları,
- seçilen malzemeler,
- koruma plakası,
- duct bank / HDD grout bölgesi,
- beton trough veya tünel kaplaması,
- duct iç/dış çapı,
- harici ısı kaynakları.

Motor şu statüde kalır:

```text
SHADOW_COMPARE
```

Proje `λ1`, IEC ampacity veya üretim termal sonucu değiştirilmez.

## 7. Nodal model kapsamı

2D sonlu-hacim modeli şunları ayrı malzeme bölgeleri olarak temsil eder:

- doğal zemin,
- yataklama,
- termal backfill,
- seçilmiş/genel dolgu,
- yüzey tabakası,
- koruma plakası,
- duct ve duct içi,
- grout/beton bank,
- beton trough duvarı ve iç ortam,
- tünel kaplaması ve iç ortam.

Beton trough ve tünel iç ortamı bu sürümde **eşdeğer iletim bölgesi** olarak ele alınır. Doğal veya zorlanmış hava dolaşımı, radyasyon ve fan havalandırması henüz çözülmez; sonuç açık uyarı taşır.

## 8. Validasyonlar

Eklenen kontroller:

- hendek genişliği/derinliği pozitifliği,
- katman toplamının hendek derinliğini aşması,
- geçersiz koruma plakası geometrisi,
- kablonun kanal sınırı dışında kalması,
- bilinmeyen termal malzeme kimliği,
- mevcut kablo çakışmaları ve duct slot çakışmaları.

## 9. Sonraki aşamalar

- arbitrary polygon malzeme bölgeleri,
- eğimli hendek duvarı,
- çok tabakalı kaya/zemin kesiti,
- kanal içi doğal/zorlanmış konveksiyon,
- termal kontur sonuçlarının aynı kanvas üzerinde gösterilmesi,
- saha ölçümü ve malzeme lotu kayıtlarının kütüphaneye bağlanması,
- nihai fiziksel motora yükseltme için IEC/CIGRE benchmark geçidi.
