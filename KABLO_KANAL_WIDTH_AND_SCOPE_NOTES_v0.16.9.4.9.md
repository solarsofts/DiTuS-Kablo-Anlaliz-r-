# v0.16.9.4.9 — Kesit ölçüsü ve kurulum kapsamı teknik notları

## Ölçü koordinatları
Ölçü çizgisi ve metni artık aynı QGraphicsScene koordinat sistemini kullanır. Metin tek başına cihaz koordinatına sabitlenmez; böylece kanal sınırı, katman sınırı ve ölçü birlikte pan/zoom yapar.

## Doğrudan gömülü hendek
- `trench_width_m`: kullanıcı tarafından girilen hendek alt genişliği.
- Fiziksel minimum: aktif kablo dış zarfı + sağ/sol bedding-sand payı.
- Daha büyük kullanıcı genişliği korunur; fiziksel minimumdan küçük değer minimuma yükseltilir.

## DUCT_BANK
- `trench_width_m`: toplam kazı alt genişliği.
- `duct_bank_width_m`: boru/grout blok genişliği.
- Önerilen kazı minimumu: blok/slot zarfı + toplam 0,30 m yan kazı payı.
- Duct slotları yalnız DUCT_BANK çiziminde görünür.

## Mimari sınır
Bu sürüm yalnız UI/render bağlarını değiştirir; solver girdileri ve hesap çekirdeği değiştirilmez.
