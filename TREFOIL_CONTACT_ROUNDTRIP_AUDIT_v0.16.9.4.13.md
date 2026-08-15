# TREFOIL temas ve koordinat round-trip denetimi — v0.16.9.4.14

## Gözlenen hata

Ø60 mm TREFOIL demeti çizimde temas halinde görünmesine rağmen termal güzergâh hesabı şu hatayı üretiyordu:

`Faz 1-2 kabloları fiziksel olarak çakışıyor: eksen mesafesi=0.0600 m, dış çap=0.0600 m`

## Kök neden

Otomatik yerleşim doğruydu: üç fazın merkez mesafesi gerçek kablo dış çapına eşitti. Ancak fiziksel kablo koordinatları Kablo-Kanal tablosunda metre cinsinden beş ondalıkla gösterilip tekrar okunuyordu.

Ø60 mm için tam TREFOIL düşey ofseti:

- `sqrt(3) × 0.060 / 2 = 0.051961524... m`

Beş ondalıklı tablo değeri:

- `0.05196 m`

Bu değer tekrar okunduğunda iki eğik merkez mesafesi:

- `0.059998679985 m`

oluyordu. Fark yalnız `1.32 µm` olmasına rağmen önceki doğrulayıcı bunu gerçek kablo zarfı penetrasyonu sayıyordu.

## Uygulanan düzeltme

1. TREFOIL seçili her devre/paralel grubu tablo değerleri okunduktan sonra grup merkezi korunarak gerçek dış çapa yeniden kilitlenir.
2. Fiziksel kablo x/depth tablosunun gösterim hassasiyeti beşten sekiz ondalığa çıkarıldı.
3. Kanvas koordinat aktarım hassasiyeti sekiz ondalığa çıkarıldı.
4. v0.16.9.4.12 ile kaydedilmiş yakın-eşkenar ve dış çapa yakın TREFOIL grupları proje açılışında otomatik onarılır.
5. Kurulum doğrulaması, IEC dış termal direnç matrisi ve 2D nodal doğrulaması aynı merkez-temas toleransını kullanır.
6. Tolerans yalnız sayısal/temsil hatasını kapsar: `max(0.020 mm, dış çap × 0.0005)`. Bunun üzerindeki gerçek penetrasyon hata olmaya devam eder.

## Sonuç

- TREFOIL merkez aralığı kullanıcı girdisi değildir; her zaman gerçek kablo dış çapından otomatik türetilir.
- Temas eden kablolar geçerlidir.
- Gerçek zarf çakışması reddedilir.
- Mevcut yuvarlanmış proje geometrisi kullanıcı müdahalesi olmadan onarılır.
