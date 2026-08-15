# DiTuS Kablo Analizör — UI Bağlantı Denetimi v0.16.2.3

## Denetim amacı

Tam-tuval ana ekran geçişinden sonra proje ağacı, modül editörleri, hesap komutları, sonuç merkezi ve modal oluşturucular arasındaki bağlantılar yeniden denetlendi. Hedef; bir ekranın başka bir pencereyi istemeden açmaması, proje ağacındaki her işlevsel düğümün gerçek bir hedefe ulaşması ve hesap öncesi/sonrası ekranların doğru sırada açılmasıdır.

## Ekran bağlantı matrisi

| Kaynak | Kullanıcı işlemi | Açılan hedef | Durum |
|---|---|---|---|
| Proje kökü | Çift tıklama | Tam Plan/CAD tuvali | PASS |
| Sistem/Yük aşaması | Çift tıklama | İlk Tasarım/System-Load ekranı | PASS |
| Güzergâh bölümü | Çift tıklama | Güzergâh editörü + ilgili satır | PASS |
| Termal ana düğüm | Çift tıklama | Termal Güzergâh editörü | PASS |
| Termal bölge | Çift tıklama | Termal Bölgeler sekmesi + ilgili satır | PASS |
| Kesit şablonu | Çift tıklama | Kesit Şablonları sekmesi + ilgili satır | PASS |
| Termal malzeme | Çift tıklama | Malzeme Kütüphanesi sekmesi + ilgili satır | PASS |
| Kablo | Çift tıklama | Kablo Kütüphanesi/Parametrik Oluşturucu | PASS |
| Termal aşama, çözüm yok | Çift tıklama | Bölge/kesit girdileri | PASS |
| Termal aşama, 2D çözüm var | Çift tıklama | Termal Alan sonuç inceleme | PASS |
| Bonding minor section | Çift tıklama | Minor Sections sekmesi + satır | PASS |
| Joint | Çift tıklama | Joint sekmesi + satır | PASS |
| Link box | Çift tıklama | Link Box sekmesi + satır | PASS |
| Arıza senaryosu | Çift tıklama | Arıza/EPR editörü + satır | PASS |
| SVL adayı | Çift tıklama | SVL editörü + aday satırı | PASS |
| Sonuç düğümü | Çift tıklama | Yalnız Sonuçlar ve Kayıtlar penceresi | PASS |
| Rapor düğümü | Çift tıklama | Yalnız Rapor Oluşturucu | PASS |
| BOQ/BOM/RFQ düğümü | Çift tıklama | Yalnız Tedarik Oluşturucu | PASS |

## Termal bölge seçim sözleşmesi

### Çözüm öncesi

Termal Alan sonuç ekranında sahte veya boş bir bölge listesi gösterilmez. Kullanıcı:

1. Termal Güzergâh Girdileri ekranında bölgeleri tanımlar.
2. Kesit şablonu ve malzemeleri bağlar.
3. Bölge doğrulamasını çalıştırır.
4. Bölgesel IEC 60287 veya 2D Nodal hesabını başlatır.

### Çözüm sonrası

- Senaryo ve bölge Termal Alan ekranındaki iki seçim alanından seçilir.
- Ayrı 2D Nodal Sonuçları tablosundan seçim yapılırsa Termal Alan seçimi güncellenir.
- Termal Alan seçimi sonuç tablosundaki satırla senkronize edilir.
- Çift tıklama Termal Analiz Detayı penceresini açar.

## Pencere açılma politikası

- **Editör komutu:** yalnız editör/modül penceresini açar.
- **Hesapla komutu:** mevcut modülde sonucu günceller; ikinci sonuç penceresi açmaz.
- **Sonuçlarını Aç komutu:** sonuç merkezini açıkça açar.
- **Sonuç tablosunda tek seçim:** başka pencere açmaz.
- **Proje ağacında tek tıklama:** yalnız seçim ve tooltip/durum hazırlığı yapar.
- **Proje ağacında çift tıklama:** hedef ekranı açar.

## Denetimde bulunan ve düzeltilen kopukluklar

1. 2D çözüm yokken Termal aşamanın boş sonuç ekranına yönlenmesi.
2. Termal bölge seçiminin yalnız ayrı sonuç penceresine bağımlı olması.
3. Hesap motorlarının ikinci Sonuçlar penceresini otomatik açması.
4. Sonuç satırı seçiminin editör penceresini otomatik açması.
5. Termal bölge/şablon/malzeme ağaç düğümlerinin işlevsiz genel düğüm olması.
6. Güzergâh, bonding, arıza ve SVL alt nesnelerinin hedef satırı seçmemesi.
7. Rapor/tedarik/wizard açılırken arkada ilgisiz modül penceresi açılması.
8. Rapor ve tedarik dosya adlarında eski sürüm sabiti bulunması.

## Bilinçli olarak sonraki sürüme bırakılanlar

v0.16.3 kapsamında Kablo, Termal Kesit, Joint/Termination, Link Box ve SVL editörleri daha küçük görev odaklı ayrı pencerelere ayrılacaktır. Mevcut büyük Proje Modülü ekranları çalışır durumdadır; bu konu bağlantı hatası değil, sonraki UX sadeleştirmesidir.
