# Yayın Veri Bütünlüğü Politikası — FAZ 1

## Denetim modeli

Ana kapı desen tabanlıdır. E-posta, kullanıcı ve mutlak disk yolları, UNC yolları, Türkiye telefon numarası, kontrol basamakları geçerli T.C. kimlik numarası, özel/yerel IPv4 adresi ve kimlik taşıyan metadata alanları taranır.

Geçmişte sızmış özel kişi, kurum veya proje değerleri açık metin kara-listesi olarak tutulmaz. Normalleştirilmiş SHA-256 regresyon parmak izleriyle kontrol edilir. İzinler yalnız belirli kural ile belirli dosya yolunun kesişiminde geçerlidir; global kelime istisnası yoktur.

## Belge kapsamı

- Düz metin ve kaynak dosyaları
- JSON içindeki kimlik alanları
- DOCX/XLSX/PPTX paketleri, üye adları, XML içerikleri ve çekirdek metadata
- PDF sayfa metni, document-info/XMP metadata, annotation, form alanı ve gömülü ekler
- Paket içindeki dosya ve arşiv üyesi adları

Açılamayan, şifreli, desteklenmeyen eski ofis biçimindeki veya beklenen metni çıkarılamayan belge yayın kapısını düşürür.

## Kabul kanıtı

`tools/run_release_acceptance.py` testleri JUnit XML ile toplar, yayın denetimini çalıştırır, hesap/model motor hash kilidini ve manifesti doğrular. Tek yapılandırılmış JSON sonucu üretilir; TXT ve MD belgeleri bu sonuçtan deterministik olarak türetilir.

v0.16.9.4.14 içindeki PDF PASS/0 eşleşme beyanları doğrulanmış kanıt değildir ve yeni otomatik denetim tarafından geçersiz kılınmıştır.
