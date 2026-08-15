# DiTuS v0.16.9 — Termal Malzeme Kütüphanesi Araştırma ve Kullanım Politikası

## Teknik hüküm

Termal kum dışında kullanılan backfill de kablo sıcaklığını ve ampacity'yi doğrudan etkiler. Etki malzemenin adına değil, yerleştirilmiş durumdaki aşağıdaki özelliklerine bağlıdır:

- ısıl özdirenç / iletkenlik,
- kuru ve ıslak durum,
- nem–yoğunluk ilişkisi,
- kompaksiyon,
- dane boyutu ve boşluk oranı,
- sıcaklık altında nem göçü ve kısmi kuruma,
- malzeme–kablo/duct temas boşlukları,
- zamanla büzülme veya ayrışma.

Bu nedenle sağlam bazalt veya kalker kaya numunesinin iletkenliği, kırılmış bazalt/kalker hendek dolgusuna doğrudan atanamaz.

## Standarda dayalı sınırlar

- IEC 60287-2-1:2023; doğrudan gömülü, duct, trough ve çelik boru kurulumlarının kararlı termal direncini, kısmi zemin kuruması bulunan ve bulunmayan koşulları kapsar.
- IEC 60853-3:2002; çevrimsel yük altında kısmi zemin kuruması beklenen durum için özel yöntem verir.
- IEEE 442-2017; toprak ve kabloyu çevreleyen beton, engineered backfill, grout, kaya, kum ve diğer malzemelerin termal özdirenç ölçümünü kapsar.
- ASTM D5334-22ae1; sağlam ve yeniden hazırlanmış toprak/kaya numunelerinde laboratuvar veya saha transient heat yöntemiyle termal iletkenlik ölçümünü tanımlar.

## Kütüphane politikası

Yerleşik kayıtlar üç sınıfa ayrılır:

1. **Referans kaya** — sağlam numune literatür değeri; hendek dolgusu olarak kullanılamaz.
2. **Ön tasarım hedefi** — kontrollü termal kum/backfill gibi satın alma veya hassasiyet hedefi; proje testi gerekir.
3. **Test zorunlu placeholder** — kırmataş bazalt, kırmataş kalker, CLSM, grout gibi karışımı ve yerleştirme koşulu projeye bağlı malzemeler.

Her kayıt şu metadata'yı taşır:

- değer ve birim,
- referans min–maks aralığı,
- nem durumu,
- test yöntemi,
- yoğunluk/kompaksiyon,
- kaynak,
- güvenilirlik,
- `requires_project_test`.

## İlk yerleşik kayıtlar

- kuru kum referansı,
- kontrollü termal kum/backfill ön tasarım hedefi,
- sağlam bazalt referansı,
- sağlam kalker/kireçtaşı referansı,
- kumtaşı referansı,
- kırmataş bazalt — test zorunlu,
- kırmataş kalker — test zorunlu,
- CLSM — test zorunlu,
- bentonit esaslı grout — kuruma/büzülme uyarılı.

Sayısal değerler katalog seçimi veya nihai rating sabiti değildir. Kütüphane ekranı bu kayıtları projeye kopyalar; mevcut proje kayıtlarını değiştirmez.

## Backfill etkisinin hesapta gösterilmesi

2D termal modelde her malzeme hücresinin iletkenliği:

\[
k=\frac{1}{\rho_{th}}
\]

olarak kullanılır. Farklı backfill seçimi doğrudan iletim matrisini değiştirir. Kablo kayıpları aynı olsa bile kablo–zemin sıcaklık farkı değişir.

Kararlı durumda düşük ısıl özdirençli ve iyi temaslı bir backfill çoğunlukla sıcaklığı düşürür; ancak yüksek özdirenç, hava boşluğu, yetersiz kompaksiyon veya kuruma performansı tersine çevirebilir. Backfill hacmi de önemlidir: küçük bir düşük-ρ cep, çevresindeki yüksek-ρ doğal zeminin dar boğazını tamamen ortadan kaldırmaz.

## Proje için önerilen test seti

Nihai tasarımda rating'i belirleyen her zemin/backfill için en az:

- yerleştirme reçetesi ve granülometri,
- kuru yoğunluk ve kompaksiyon,
- doğal/tasarım nemi,
- kuru sınır termal özdirenci,
- nem–termal özdirenç eğrisi,
- kritik kuruma sıcaklığı veya dry-out davranışı,
- mümkünse saha yerleşim sonrası doğrulama,
- lot/numune izlenebilirliği

tutulmalıdır.

## Kaynaklar

- IEC 60287-2-1:2023 — Electric cables, current rating, thermal resistance.
- IEC 60853-3:2002 — Cyclic rating with partial drying of soil.
- IEEE 442-2017 — Thermal resistivity measurements of soils and backfill materials.
- ASTM D5334-22ae1 — Thermal conductivity of soil and rock by transient heat method.
- Balkan, Erkan & Şalk (2017), Thermal conductivity of major rock types in western and central Anatolia regions, Turkey.
- USGS/DOE rock thermal-property compilations.

## Uygulamadaki açık sınır

v0.16.9 henüz nem göçünü veya sıcaklığa bağlı iki durumlu dry-out alanını dinamik olarak çözmez. Kuru/ıslak değerler ve kritik sıcaklıklar kayıt altına alınır; IEC 60853-3 ve gelişmiş hidro-termal bağlantı sonraki hesap kapısıdır.
