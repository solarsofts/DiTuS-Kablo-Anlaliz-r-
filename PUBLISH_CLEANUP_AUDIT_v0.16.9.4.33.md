# Yayın Veri Bütünlüğü Denetimi — v0.16.9.4.33

- Sonuç: **PASS**
- Kural seti: `DITUS_PUBLISH_INTEGRITY_PHASE1_V1`
- Kural seti SHA-256: `660bbba2783faa1ee86c567602466d1cf72724a9d1dc3f77ed1ded298953b536`
- Engelleyici eşleşme: 0
- İzin verilen, konuma bağlı eşleşme: 8
- Taranamayan nesne: 0

## Kapsama kanıtı

- Dosya adı/yolu: 412/412
- Metin dosyası: 389
- Metin karakteri: 7635733
- PDF: 2/2
- PDF sayfası: 19/19
- PDF metin karakteri: 41474
- PDF metadata alanı: 18
- PDF annotation/form/ek: 0/0/0
- OOXML dosyası: 3
- Arşiv üyesi: 51

## Politika

Genel desenler e-posta, yerel veya mutlak dosya yolu, Türkiye telefon numarası, doğrulanmış T.C. kimlik numarası ve özel/yerel IP sınıflarını kapsar. Kimlik taşıyan metadata alanları ayrıca denetlenir. Geçmiş sızıntılar açık metin kara-listesi yerine SHA-256 regresyon parmak izleriyle korunur. İzinler yalnız tam kural ve tam dosya yolu kapsamındadır.

PDF denetimi `pypdf` ile sayfa metni, metadata, annotation, form alanı ve gömülü ek yüzeylerini kapsar. Açılamayan, şifreli veya metni çıkarılamayan PDF başarı sayılmaz.

## Tarihsel düzeltme

`PACKAGED_TEST_RESULTS_v0.16.9.4.14.txt` ve `PUBLISH_CLEANUP_AUDIT_v0.16.9.4.14.md` içindeki PDF taraması iddiaları bu denetimin kanıtı olarak kullanılmamıştır; doğrulanmamış tarihsel kayıtlardır ve bu otomatik denetim tarafından geçersiz kılınmıştır.

## İzin verilen eşleşmeler

- `regression_approved_designer_signature` · `EVENING_ACCEPTANCE_CHECKLIST_v0.16.9.4.15.md` · 2 eşleşme · konuma bağlı onay
- `regression_approved_designer_signature` · `IDENTITY_SIGNATURE_AUDIT_v0.16.9.4.15.md` · 1 eşleşme · konuma bağlı onay
- `regression_approved_designer_signature` · `RELEASE_NOTES_v0.16.9.4.15.md` · 1 eşleşme · konuma bağlı onay
- `regression_approved_designer_signature` · `src/ucd/ui/main_window.py` · 2 eşleşme · konuma bağlı onay
- `regression_approved_designer_signature` · `tests/test_ui_full_canvas_contract.py` · 2 eşleşme · konuma bağlı onay
