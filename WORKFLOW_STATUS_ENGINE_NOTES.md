# Merkezi Workflow Durum Motoru

## Dört ayrı boyut

Proje ağacı durumu tek bir elle güncellenen etiket değildir. Her aşama aşağıdaki dört boyuttan türetilir:

| Boyut | Değerler | Soru |
|---|---|---|
| Girdi hazırlığı | `MISSING / PRELIMINARY / COMPLETE` | Gerekli veri var mı? |
| Çalıştırma | `NOT_RUN / RUNNING / SUCCESS / FAILED` | Motor çalıştı mı? |
| Güncellik | `CURRENT / STALE / NOT_APPLICABLE` | Sonuç mevcut girdilerle aynı mı? |
| Olgunluk | `SCREENING / CONDITIONAL / VERIFIED` | Nihai tasarıma ne kadar yakın? |

Ağaç kısa birleşik ifadeyi gösterir. Tooltip ve Aşama Rehberi dört boyutu ayrı ayrı gösterir.

## Girdi imzası

Her motor bütün projeyi değil yalnız ilgili bileşenleri SHA-256 ile imzalar. Böylece rapor başlığı değişince termal çözüm stale olmaz; kablo, termal kesit veya bonding kaybı değişince olur.

## Çalışma kaydı

Her motor kaydı şunları içerir:

- yöntem,
- başlangıç/bitiş zamanı,
- girdi ve bileşen imzaları,
- sonuç/uyarı sayısı,
- hesap ön kontrolü,
- varsayım ve eksik doğrulamalar,
- stale gerekçesi.

Kayıt sayısal hesap sonucunun yerine geçmez; yalnız workflow, güncellik ve izlenebilirlik sözleşmesidir.

## Eski proje davranışı

Eski projede çalışma kaydı yoksa program girdileri değerlendirir:

- zorunlu girdiler yeterliyse `Hazır`,
- eksikse `Eksik/Bloke`,
- sonuç nesnesi oturumda mevcutsa geçici olarak `Tamamlandı` gösterir.
