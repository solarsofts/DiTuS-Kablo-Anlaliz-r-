# Kimlik ve İmza Denetimi — v0.16.9.4.15

## Yetkili uygulama imzası

Uygulama kimliği olarak yalnız aşağıdaki görünür imza kullanılır:

`designed by S.Esim & gpt`

Göründüğü yerler:

1. Ana pencere durum çubuğunun kalıcı sağ alanı.
2. Yardım → Hakkında diyaloğunun son satırı.

İmza sentetik demo raporunun işveren, yüklenici, hazırlayan veya kontrol eden metadata alanlarına yazılmaz.

## Demo metadata sonucu

- İşveren: `Sentetik 20 km Örnek Hat`
- Hazırlayan: boş (`—` olarak render edilir)
- Kontrol eden: `Teknik kontrol bekliyor`
- Proje veri imzası: `554e59e354dbf70bdb2bc8e79d25d4f59dcd6fc3f739d2d6af5cacdef79104c0`

## Yayın testi sınırı

v0.16.9.4.14 içindeki kara-liste tabanlı yayın temizliği test dosyası tamamen kaldırılmıştır. Bu sürümde onun yerine yeni bir kara liste, gizlenmiş string birleştirmesi veya eşdeğer negatif kimlik testi eklenmemiştir. Yeni yayın temizliği sözleşmesi ayrı fazda belirlenecektir.

## Motor değişmezliği

- `src/ucd/calculations/**/*.py`: byte düzeyinde değişmedi.
- `src/ucd/models/**/*.py`: byte düzeyinde değişmedi.
- Proje şeması: `0.16.4`.
- Kurulum/geometri model revizyonu: `0.16.9.4.14`.
