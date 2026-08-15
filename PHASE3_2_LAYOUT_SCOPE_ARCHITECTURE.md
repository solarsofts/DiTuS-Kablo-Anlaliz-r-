# FAZ 3.2 — Yerleşim ve analitik model kapsamı

## Koordinat sözleşmesi

- `burial_depth_m`, formasyondaki en sığ aktif kablo eksenidir.
- `phase_spacing_m`, komşu faz eksenlerinin merkezden merkeze aralığıdır.
- VERTICAL analitik koordinatları `(0,d)`, `(0,d+s)`, `(0,d+2s)` olarak kurulur.
- TREFOIL, FLAT ve VERTICAL göreli faz slotları `phase_geometry.py` içindeki ortak üreticiden gelir.
- CUSTOM, gerçek x-y koordinatlarını kullanır; koordinat yoksa `CUSTOM_POSITIONS_REQUIRED` üretilir.
- DUCT_BANK bir faz formasyonu değil, kurulum tipidir. Legacy DUCT_BANK formasyonu gerçek x-y varsa CUSTOM'a dönüştürülür; Flat'e sessiz dönüşüm yoktur.

## Analitik dış termal model kapsamı

`AUTO_IMAGE` ve `AUTO_MIXED_ZONE` yalnız `DIRECT_BURIED` kurulumunda geçerlidir.

Aşağıdaki kurulumlar nodal model veya kaynaklandırılmış pozitif manuel T4 ister:

- `DUCT_BANK`
- `HDD`
- `CONCRETE_TROUGH`
- `TUNNEL`

Geçersiz kombinasyon `ANALYTIC_MODEL_SCOPE_REQUIRES_NODAL` koduyla, `MODEL_SCOPE` anlamında ve `physical_rejection=False` olarak bölüm hücresine yazılır. Bu durum tek başına `UYGUN_DEGIL` üretmez; sonuç `INDETERMINATE` kalır.

## Bonding kapsamı

- Basit analitik bonding ve primitive ağ VERTICAL fallback geometrisini ortak faz-slot üreticisinden alır.
- SINGLE bonding, dönüş yolu/çok iletken geometrisi olmadan çözülmez ve `BONDING_SINGLE_REQUIRES_RETURN_PATH_GEOMETRY` üretir.
- Gerçek kanal x-y geometrisinin bonding ağına tam aktarılması bu fazın kapsamında değildir.

## Kullanıcı arayüzü

- Formasyon seçicisinden DUCT_BANK kaldırılmıştır.
- DUCT_BANK yalnız kurulum tipi olarak seçilir.
- Faz aralığı alanı yalnız FLAT/VERTICAL için görünürdür.
- Duct satır/sütun alanları kurulum tipine göre görünürdür.
- Özel kurulum tipi seçildiğinde kullanıcıya nodal veya manuel T4 gerekliliği erken bildirilir.
- Hesap katmanındaki model-kapsam kapısı bağlayıcıdır; UI uyarısı onu ikame etmez.

## Kapsam dışı

- IEC 60287 duct analitik T4 denklemleri
- HDD/tünel/kanal için yeni termal denklemler
- Tek fazlı bonding dönüş yolu modeli
- Fiziksel x-y kanal geometrisinin bonding ağına tam bağlanması
- Yeni nodal sınır koşulları
