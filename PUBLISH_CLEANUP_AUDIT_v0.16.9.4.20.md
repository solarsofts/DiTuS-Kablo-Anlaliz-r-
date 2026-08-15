# Paket Kabul ve Yayın Veri Bütünlüğü — v0.16.9.4.20

## Genel sonuç: **PASS**

| Kapı | Sonuç | Kanıt |
|---|---:|---|
| Pytest | PASS | 407/407 PASS, 0 skipped |
| Yayın veri bütünlüğü | PASS | 0 blocker, 8 konuma bağlı izin |
| Hesap/model motor kilidi | PASS | 41/41 dosya byte doğrulandı |
| Manifest | PASS | 304/304 |
| Kabul belgeleri öz-denetimi | PASS | JSON/TXT/MD yeniden tarandı |

## PDF kapsam kanıtı

- PDF dosyası: 2/2
- PDF sayfası: 17/17
- Çıkarılan PDF metni: 38279 karakter
- PDF metadata alanı: 18
- PDF annotation/form/ek: 0/0/0
- Taranamayan nesne: 0

## Denetim sözleşmesi

Genel desenler ve kimlik metadata kontrolleri ana kapıdır. Geçmiş sızıntılar SHA-256 regresyon parmak izleriyle tamamlayıcı olarak izlenir. İzinler yalnız belirli kural ve belirli dosya yolunda geçerlidir. PDF açılamaz, şifreliyse veya metin çıkarımı boş kalırsa denetim fail-closed davranır.

Yeni kabul belgeleri tek yapılandırılmış JSON sonucundan otomatik türetilmiştir. Manifest, kendisi ile sonradan üretilen kabul attestasyonlarını çevrimsel hash bağı nedeniyle kapsam dışında bırakır; bu üç attestasyon ayrıca yayın tarayıcısıyla öz-denetlenir.

## Tarihsel düzeltme

`PACKAGED_TEST_RESULTS_v0.16.9.4.14.txt` ve `PUBLISH_CLEANUP_AUDIT_v0.16.9.4.14.md` içindeki PDF PASS/0 eşleşme beyanı doğrulanmamıştı. Bu paket o beyanı kanıt kabul etmez ve otomatik sonuçla geçersiz kılar.

_Bu belge `tools/run_release_acceptance.py` tarafından otomatik üretilmiştir._
