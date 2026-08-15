# v0.6 SVL Design and Selection Notes

## 1. Girdi kaynağı ayrımı

SVL seçim motoru iki veri grubunu ayırır:

### Yazılımın ürettiği

- bonding çözümündeki maksimum normal metalik kılıf gerilimi,
- SVL bulunan link box'lar içindeki en uzun bonding lead,
- lead endüktansı ve girilen `di/dt` üzerinden endüktif gerilim katkısı.

### Harici doğrulama gerektiren

- fault-TOV rms gerilimi ve süresi,
- lightning/switching residual-voltage değerlendirme noktası,
- SVL enerji gereksinimi,
- deşarj akımı,
- transient akım yükselme hızı,
- joint interrupt ve dış kılıf darbe dayanımı,
- üretici MCOV/TOV/V-I/enerji eğrileri.

Harici büyüklükler eksikse motor bunları uydurmaz.

## 2. Sürekli gerilim görevi

```text
Ucontinuous,required = max(Unormal, Uemergency) × (1 + margin)
Uemergency = Unormal × emergency_multiplier
```

Adayın MCOV değeri bu görevden küçükse aday `FAIL` olur.

## 3. Fault-TOV

Aday veri modelinde 1 s, 10 s ve 100 s rms TOV dayanım noktaları vardır. İstenen süre bu aralıkta ise gerilim, log-zaman ekseninde doğrusal interpolasyonla bulunur. Süre aday eğrisinin dışında ise ekstrapolasyon yapılmaz; kontrol `CONDITIONAL` kalır.

## 4. Bonding-lead gerilimi

En uzun SVL lead için:

```text
Vlead,peak = Llead × di/dt
Llead = lead_inductance_per_m × lead_length
```

Birim dönüşümleri hesap çekirdeğinde yapılır. Bu terim residual voltage üzerine eklenir.

## 5. Yalıtım koordinasyonu

```text
Uprotective,peak = Uresidual,peak + Vlead,peak
Uallowed,peak = min(BILjoint, BILjacket) × utilization_fraction
```

`Uprotective > Uallowed` ise aday `FAIL` olur. Bu ön kontrol frequency-dependent EMT'nin yerine geçmez.

## 6. Enerji ve deşarj akımı

```text
Erequired,design = EEMT × (1 + energy_margin)
```

Aday enerji kapasitesi ve nominal deşarj akımı ayrı ayrı kontrol edilir. Girdi yoksa ilgili kontrol bekleyen olarak işaretlenir.

## 7. Sonuç sınıfları

- `PASS`: tüm değerlendirilmiş zorunlu kontroller uygun ve bekleyen kontrol yok.
- `CONDITIONAL`: başarısız kontrol yok, fakat eksik görev veya aday verisi var.
- `FAIL`: en az bir zorunlu kontrol başarısız.

Sıralama önce durum sınıfına, sonra tamamlanan kontrollerin sayısına, ardından gereksiz MCOV büyüklüğünün azaltılmasına göre yapılır.

## 8. Link-box ataması

Önerilen aday otomatik olarak yalnız `contains_svl=True` olan link box'lara atanır. Link-box tablosu aday kimliğini saklar. Atama, üretici onayı veya satın alma kararı anlamına gelmez.

## 9. Mevcut sınır

v0.6 motoru duty-envelope tabanlı seçim/koordinasyon katmanıdır. Lightning/switching/fault dalga şekillerini üretmez ve nonlinear MOV enerji integrasyonu yapmaz. Bu görevler sonraki frequency-dependent EMT katmanına aittir.
