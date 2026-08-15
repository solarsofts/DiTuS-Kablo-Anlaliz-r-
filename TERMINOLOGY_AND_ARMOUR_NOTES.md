# DiTuS Kablo Analizör v0.14.2 — Terminoloji ve zırh ayrımı

## Bağlayıcı kullanıcı arayüzü terminolojisi

- `sheath`: **metalik kılıf/ekran**
- `metallic screen`: **metalik ekran**
- `outer sheath / jacket`: **dış kılıf**
- `armour`: **zırh**

Metalik kılıf/ekran ile zırh aynı katman değildir. Cross-bonding, SVL, metalik kılıf gerilimi, dolaşım akımı ve IEC 60287 `λ1` metalik kılıf/ekran için kullanılır. `λ2` yalnız kablo konstrüksiyonunda gerçek bir zırh katmanı bulunuyorsa zırh kaybını temsil eder.

İç JSON alan adları ve Python API'sindeki `sheath_*` / `armour_*` adları eski proje uyumluluğu için değiştirilmemiştir. Kullanıcıya gösterilen metinler Türkçeleştirilmiştir.

## Yeni doğrulamalar

- Zırh katmanı olmadan `λ2 > 0` girilirse uyarı verilir.
- Zırh katmanı varken `λ2 = 0` ise zırh kaybının hesap dışı veya doğrulanmamış olduğu belirtilir.
- Metalik ekran/kılıf bulunmaması bonding modeli için ayrı hata olarak kalır.
