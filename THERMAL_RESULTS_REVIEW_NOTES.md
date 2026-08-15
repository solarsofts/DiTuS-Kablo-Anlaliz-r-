# v0.12.1 Termal Sonuç İnceleme ve Hotfix Notları

## Amaç

v0.12.0 2D nodal hesap çekirdeğinin sonuçlarını bölge ve yük senaryosu bazında açık, izlenebilir ve denetlenebilir hale getirmek. Sayısal çözüm denklemleri değiştirilmemiştir.

## Tek kayıt anahtarı

Arayüzdeki bütün seçimler şu anahtarı kullanır:

```text
(scenario_id, region_id)
```

Bölge ağacı, karşılaştırma tablosu, sıcaklık alanı ve sonuç denetçisi birbirinden bağımsız kopyalar üretmez; aynı `NodalRegionResult` nesnesini gösterir.

## Görsel katmanlar

- Sıcaklık rasterı: çözülen hücre-merkezli sıcaklıklardan
- Malzeme sınırları: komşu hücrelerin `material_id` değişimlerinden
- Kablo merkezleri ve sıcaklıkları: `NodalCableResult`
- Hendek/su bindirmesi: seçili termal bölgenin şablon ve override verilerinden
- Mesh: sayısal ağ kenarlarından, isteğe bağlı
- İzoterm: sıcaklık bantları arasındaki hücre sınırlarından oluşturulan yaklaşık kontrol çizgileri
- Sıcak nokta: sıcaklık matrisi maksimum hücresinden

Yaklaşık izotermler görsel kontrol içindir; yeni bir sayısal çözüm veya interpolasyon standardı değildir.

## Yalancı mesh çizgisi hotfix'i

v0.12.0'da her sıcaklık hücresi ayrı `QGraphicsRectItem` olarak çiziliyordu. Antialiasing, bitişik hücreler arasında gerçekte bulunmayan ince beyaz çizgiler oluşturabiliyordu. v0.12.1'de alan tek `QImage/QPixmap` rasterına çizilir; gerçek mesh yalnız kullanıcı açtığında ayrı katman olarak gösterilir.

## Bölge karşılaştırma sırası

Aktif yük senaryosu önce gösterilir. Aynı senaryoda bölgeler:

```text
ampacity marjı = Iampacity,2D − Iyük
```

artan sıralanır. Böylece en düşük marjlı güzergâh bölümü en üstte görünür. Güzergâhı sınırlayan kritik bölge ayrıca yıldızla işaretlenir.

## Mesh yakınsama kapısı

Seçili bölge:

- kaba mesh ölçeği `1.25`
- inceltilmiş mesh ölçeği `0.75`

ile yeniden çözülür. Maksimum iletken sıcaklığı farkı raporlanır. Arayüz varsayılan kabul eşiği `%1`'dir. Bu kontrol fiziksel model doğrulaması değildir; yalnız sayısal ağ duyarlılığını gösterir.

## Korunan sınırlar

- Model güzergâha dik, kararlı durum 2D orta kesittir.
- HDD giriş/çıkışları ve kısa kesit geçişleri 3D değildir.
- IEC 60853 transient/cyclic rating bu hotfix kapsamına eklenmemiştir.
- Malzeme kaynak ve güven durumu değişmeden korunur.
