# DiTuS Kablo Analizör v0.16.9.4.37

## Bonding zoom alt sınırı

Bonding diyagramında wheel ile zoom-out, tüm bonding kompozisyonunun viewport'a sığdığı `fit-to-content` ölçeğinde durur. Kullanıcı zoom-in yapabilir; fakat tam görünümden daha küçük anlamsız ölçeğe inmeye devam edemez.

## Standart sabit / katsayı yönetişimi

v0.16.9.4.35'te desteklenen Milliken `ks/kp` çiftlerini otomatik resolver'dan kaldıran değişiklik geri alınmıştır. Desteklenen yuvarlak konstrüksiyonlarda `ks/kp` tekrar standart-kaynaklı resolver ile otomatik çözülür. Cu Milliken profili bilinmiyorsa tahmin yapılmaz; açık kullanıcı/üretici çifti resolver'ın önüne geçer.

Ayrıca v0.16.9.4.35'te eklenen `StandardDefaults` profilinin eksik alanlarını bütün hesap motorları için global zorunlu kapı yapan davranış kaldırılmıştır. Zemin, ortam, derinlik ve dielektrik gibi proje/site/malzeme verileri aktif proje kaynaklarından gelir. Ön tanım profili yalnız isteğe bağlı kullanıcı/kurum profili olarak kalır.

## Fizik kapsamı

- IEC skin/proximity denklem yapısı değişmedi.
- Bonding, global primitive ağ, termal, transient, fault/EPR, SVL ve sheath-loss completeness motorları değiştirilmedi.
- Fizik davranışındaki tek bilinçli değişiklik, v0.16.9.4.35'te kaldırılmış olan desteklenen `ks/kp` otomatik resolver'ının geri getirilmesidir.

Ayrıntı: `FIXED_VALUE_AUDIT_v0.16.9.4.37.md`.
