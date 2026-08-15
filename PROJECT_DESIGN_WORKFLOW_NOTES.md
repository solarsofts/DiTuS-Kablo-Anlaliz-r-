# Proje Tasarım Akışı ve Motor Veri Kapıları

## Tasarım ilkesi

DiTuS ana arayüzü hesap motorlarının adlarına göre değil, yeraltı kablo mühendisinin karar sırasına göre düzenlenir. Bir motor yalnız gerekli aşamada kullanıcıdan veri ister. Başlangıç ekranında SVL, bonding lead, transient mesh veya gelişmiş toprak dönüş parametreleri sorulmaz.

## Aşama sözleşmesi

Her aşama beş grubu görünür kılar:

1. Kullanıcının tanımlayacağı veriler
2. Çalışacak hesap/doğrulama motorları
3. Eksik veya bloke eden girdiler
4. Üretilecek sonuçlar
5. Önerilen sonraki işlem

Aşamalar kilitli bir sihirbaz değildir. Kullanıcı proje ağacı veya üst aşama şeridinden istediği bölüme geçebilir. Ancak `BLOCKED` ve `MISSING_DATA` kapıları, erken çalıştırılan motorun neden nihai sonuç veremeyeceğini açıklar.

## Motor–aşama eşleşmesi

| Aşama | Motorlar | Ana veri kapısı |
|---|---|---|
| Sistem/yük | Yük ve tasarım akımı | Gerilim, frekans, MW/MVA/A, güç faktörü, devre/N-1 |
| Güzergâh | Chainage/kapsam doğrulama | Pozitif uzunluk, bölge sınırları, geçişler |
| Kurulum | Termal kesit ve T1–T4 ön işlemi | Derinlik, aralık, toprak/backfill, veri kaynağı |
| Kablo | Katalog ve parametrik doğrulama | U0/U(Um), kesit, malzeme, ekran, snapshot |
| Ön eleme | Akım, gerilim düşümü, katalog benchmark | Tasarım akımı ve kablo adayı |
| Sürekli termal | IEC 60287 + 2D nodal | Kablo geometrisi ve bölgesel termal veriler |
| Bonding | Loop + primitive CIM/NV | Joint/minor section, link box, topraklama, ECC/GCC |
| Arıza/EPR | 3PH/PP/SLG + EPR | Z1/Z0, temizleme süresi, ekran ve topraklama |
| SVL | MCOV/TOV/residual/enerji | Arıza sonucu, yalıtım seviyeleri, lead ve aday verileri |
| IEC 60853 | Transient/cyclic/emergency | Yük-zaman profili ve ısıl kapasite |
| İterasyon | Birleşik tasarım zinciri | Önceki aşamaların kapıları ve kabul kriterleri |
| Çıktılar | Rapor + BOQ/BOM/RFQ | Doküman, metraj ve tedarik varsayımları |

## Güncellik

Kablo veya güzergâh değiştiğinde bağlı hesaplar `STALE` olur. Eski sonuçlar silinmez; fakat güncel tasarım sonucu gibi gösterilmez. Yeni akış değerlendirme motoru runtime hesap sonuçlarını proje şemasına sahte veri olarak yazmaz.

## Ayrı editörlere geçiş

v0.16.3 ile ayrıntılı eleman editörleri ayrı pencere olacaktır. Ana ekran yalnız özet, atama, hazırlık durumu ve “Düzenle” eylemini gösterecektir. Editör kaydı sonrasında etkilenen motorlar otomatik `STALE` yapılacaktır.
