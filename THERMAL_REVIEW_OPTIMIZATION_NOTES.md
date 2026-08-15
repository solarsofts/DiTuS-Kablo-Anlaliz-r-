# v0.13.1 — Birleşik Termal İnceleme ve Optimizasyon Hotfix Notları

## Amaç

v0.12.1/v0.13.0 termal çalışma alanında aynı bölge/senaryo kaydı üstte ayrı ağaç, sağda sürekli açık denetçi ve altta sonuç tablosunda tekrar ediyordu. Bu düzen sıcaklık alanını küçültüyor, sonuçları yatayda okunamaz hale getiriyor ve seçim kaynağını belirsizleştiriyordu.

v0.13.1, mevcut 2D kararlı ve IEC 60853 geçici hesap çekirdeklerini değiştirmeden termal incelemeyi tek kayıt/tek seçim mimarisine taşır ve bölgesel tasarım alternatiflerini gerçek 2D yeniden çözümle değerlendirir.

## Ana ekran

- Termal Alan sekmesindeki bölge/senaryo ağacı kaldırıldı.
- Sürekli açık sonuç denetçisi kaldırıldı.
- Termal Alan sekmesindeki ikinci karşılaştırma listesi kaldırıldı.
- Tek seçim kaynağı alt bölümdeki `2D Nodal Sonuçları` tablosudur.
- Tablo yalnız ana karar sütunlarını içerir: senaryo, bölge, chainage, kurulum, yük, 2D ampacity, marj, maksimum iletken sıcaklığı ve durum.
- Satır seçimi sıcaklık alanını günceller; çift tıklama ayrıntılı termal analiz penceresini açar.
- Termal Alan görünümü tam genişliğe çıkarılmıştır.

## Termal Analiz Detayı penceresi

Bağımsız ve yeniden boyutlandırılabilir pencere şu sekmeleri içerir:

1. **Özet** — bölge, chainage, senaryo, yük, ampacity, sıcaklık, marj ve hüküm.
2. **Kesit / Sıcaklık Alanı** — büyük 2D alan, malzeme sınırları, hendek/su, kablolar, mesh, izoterm ve sıcak nokta katmanları.
3. **Girdiler ve Kaynaklar** — uygulanan şablon, geometri, zemin/dolgu özellikleri, DESIGN/TESTED/AS_BUILT ve kaynak izleri.
4. **Enerji / Mesh Doğrulama** — enerji dengesi, residual, iterasyon, mesh kapsamı ve varsa mesh yakınsama sonucu.
5. **IEC 60287 / 2D Karşılaştırma** — ampacity farkı ve kablo bazlı sıcaklık/kayıp sonuçları.
6. **Transient / Cyclic** — aynı bölgenin IEC 60853 yük-zaman grafiği, çevrimsel ve acil rating sonuçları.
7. **Tasarım Değişikliği Önerileri** — gerçek 2D nodal yeniden çözüm sonuçları.

## Bölgesel tasarım alternatifleri

Seçili bölge ve yük senaryosu için kurulum tipine göre uygulanabilir adaylar üretilir:

- Doğal zemin ısıl özdirencinin iyileştirilmesi
- Kablo çevresi termal dolgu ısıl özdirencinin iyileştirilmesi
- Termal dolgu/hendek hacminin büyütülmesi
- Gömülme derinliğinin azaltılması
- Faz aralığının artırılması
- Duct bank/HDD için grout ısıl özdirencinin iyileştirilmesi
- Duct iç çapı ve bank genişliğinin değiştirilmesi

Her aday için seçili bölge tekrar çözülür ve şu sonuçlar gösterilir:

- Yeni 2D ampacity
- Ampacity artışı/azalışı
- Maksimum iletken sıcaklığı değişimi
- Yeni akım marjı
- Uygunluk/iyileşme/olumsuzluk durumu
- Solver uyarıları

Bir alternatif uygulandığında yalnız seçili termal bölgenin `overrides` alanı güncellenir; diğer bölgeler değişmez. Mevcut hesap sonuçları geçersiz kılınır ve kullanıcıdan IEC 60287, 2D nodal ve IEC 60853 çalışmalarını yeniden çalıştırması istenir.

## Açık sınırlar

- Öneriler termal etkileri yeniden hesaplar; mekanik koruma, kazı uygulanabilirliği, elektromanyetik aralık, kablo çekme, inşaat maliyeti ve izin koşulları ayrıca doğrulanmalıdır.
- HDD giriş/çıkışı, joint bay, menhol ve eksenel geçişler 3D değildir.
- IEC 60853-3 kısmi kuruma/yeniden ıslanma modeli henüz yoktur.
- Üretici kablo katalogları ve gerçek saha/laboratuvar zemin verileri girilmeden sonuçlar ön tasarım olgunluğundadır.
