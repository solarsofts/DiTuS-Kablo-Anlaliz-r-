# FAZ 2 — Katalog ve Parametrik Geometri Mimarisi

## Dağıtım modeli

DiTuS açık kaynak paketi üretici katalog verisi taşımaz. Kullanıcı kayıtları uygulama veri dizininde tutulur; dışa aktarılan `.ditus-cable-catalog.json` paketleri kullanıcı tarafından paylaşılabilir. Paket içindeki `src/ucd/resources/catalogs/` dizini üretici satırı içermez.

## Tek yönlü veri zinciri

```text
kesit + malzeme + sıkıştırma profili
→ fiziksel iletken zarfı
→ iç yarı iletken
→ gerilim profili izolasyonu
→ dış yarı iletken ve bantlar
→ metalik ekran/sheath
→ profil formülünden dış kılıf
→ hesaplanmış dış çap
→ katmanlardan skaler senkronizasyon
```

Yayımlanmış dış çap ve kg/km değerleri geometriyi değiştiren girdiler değildir; yalnız CAT sınıfı doğrulama kanıtıdır.

## Kaynak sınıfları

- `STANDARD_DERIVED`: standarda bağlı profil ve merkezi malzeme değeri.
- `CALCULATED`: katman çapı, ekran geometrisi, dış çap ve hesaplanan kütle.
- `USER_ASSUMPTION`: yarı iletken/bant kalınlığı, sıkıştırma ve YG sheath ayrıntısı.
- `CATALOG`: yalnız kullanıcı tarafından girilen yayımlanmış üretici değeri.

Paketlenmiş jenerik şablonlarda `CATALOG` kaynağı bulunmaz.

## Doğrulama kapıları

- Dış çap toleransı: büyük olan `2,0 mm` veya `%5`.
- Kütle toleransı: büyük olan `50 kg/km` veya `%10`.
- Her katmanın iç çapı önceki katmanın dış çapına eşit olmalıdır.
- Herhangi bir kapı başarısızsa kayıt `CONDITIONAL` kalır; hesaplanan, yayımlanmış ve sapma değerleri kayıt izine yazılır.

Bu toleranslar FAZ 2 yazılım kapılarıdır; ürün standardı uygunluk sınırı veya üretici kabul kriteri değildir.
