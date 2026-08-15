# Kablo-Kanal Düzeni — Duct ve Katman UX Notları v0.16.9.4.3

## Duct bank bağlantı zinciri

Sağ panelde `Boru / kanal yerleşimi (DUCT BANK)` seçimi artık yalnız `arrangement_label` değiştirmez. Aşağıdaki zincir birlikte yenilenir:

```text
Formasyon = DUCT_BANK
→ Installation type = DUCT_BANK
→ devre × paralel × 3 adet gerekli kablo
→ duct satır/sütun kapasitesi
→ gerekirse satır sayısının otomatik artırılması
→ her slot için iç/dış çap ve x-y merkez koordinatı
→ her fiziksel kablonun bir duct slotuna atanması
→ ölçekli kanal çizimi
```

## Ölçek

- Kablo çapı: proje kablosunun `overall_diameter_mm` değeri.
- Duct dış çapı: `DuctSlotData.outer_diameter_m`.
- Duct iç çapı: `DuctSlotData.inner_diameter_m`.
- Hendek, bank, duct ve kablo aynı `px/m` dönüşümüyle çizilir.

## Katman rolleri

Katman rolü ile gerçek termal malzeme kaydı ayrıdır. Örneğin `BEDDING_SAND` bir geometrik roldür; bağlı malzeme `MAT-TB-01` veya kullanıcı tarafından seçilen başka bir kayıt olabilir.

Genel üst dolgu kalınlığı otomatik hesaplanır:

```text
general backfill = trench depth
                 - surface layer
                 - selected backfill
                 - thermal backfill
                 - bedding sand
```

Negatif sonuç sıfıra sınırlandırılır; ayrıca ana geometri doğrulaması katman toplamının hendek derinliğini aşmasını hata olarak raporlar.

## Görsel politika

- Varsayılan görünümde yalnız fiziksel yapı, fazlar ve zorunlu ölçüler görünür.
- Katman içi büyük yazılar ve lejant varsayılan kapalıdır.
- Kullanıcı `Detay yazıları` ile açıklama katmanını açabilir.
- Katman renkleri kullanıcı tercihidir; solver girdisi değildir.
