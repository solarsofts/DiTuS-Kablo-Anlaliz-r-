# DiTuS Kablo Analizör v0.16.9.4.16 — Yayın Veri Bütünlüğü FAZ 1

## Değişiklikler

- Kara-liste merkezli eski yayın testi yerine genel desenler, metadata denetimi, dar konum izinleri ve SHA-256 regresyon parmak izlerinden oluşan hibrit kapı eklendi.
- PDF okuma tarafına `pypdf` eklendi. Sayfa metni, document-info/XMP metadata, annotation, form alanı ve gömülü ekler taranır.
- PDF açılamaz, şifreliyse veya metin çıkarımı boşsa sonuç fail-closed olur.
- DOCX/XLSX/PPTX arşiv üyeleri ve çekirdek kimlik metadata alanları taranır.
- Test, yayın taraması, motor hash kilidi ve manifest sonucu tek JSON kabul kaydında birleştirilir; TXT/MD belgeleri otomatik üretilir.
- Sentetik örnek üreticisinde paketlenmiş mutlak çalışma makinesi yolu kaldırıldı ve paket köküne göreli çözüm kullanıldı.
- v0.16.9.4.14 kabul belgelerindeki doğrulanmamış PDF PASS beyanı yeni belgelerde açıkça geçersiz kılındı.

## Korunan taban

- `src/ucd/calculations` ve `src/ucd/models`: v0.16.9.4.15 ile byte-identical
- Proje şeması: `0.16.4`
- Hesap motorları ve veri modelleri: değişmedi
