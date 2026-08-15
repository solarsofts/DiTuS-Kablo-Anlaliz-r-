# DiTuS Kablo Analizör v0.16.9.4.15 — Kimlik ve İmza Hotfix

## Kapsam

Bu sürüm yalnız yayın kimliği, uygulama imzası ve bunlardan etkilenen sentetik demo raporu çıktılarıyla sınırlıdır. Hesap motorları, proje veri şeması, kablo-kanal geometrisi ve hesap sonucu üretim denklemleri değiştirilmemiştir.

## Değişiklikler

- `tests/test_publish_clean_v0169414.py` paketten çıkarıldı. İçindeki string-birleştirmeli kara liste ve kara-liste yaklaşımı bu sürümde başka bir teste taşınmadı.
- `STANDARDS_SCOPE.md` içindeki v0.14.1 başlığı ve açıklaması yayın veri bütünlüğünü anlatan nötr metne dönüştürüldü.
- Sentetik 20 km demo raporunda işveren alanı `Sentetik 20 km Örnek Hat` oldu.
- Sentetik demo metadata'sındaki `prepared_by` değeri boş bırakıldı. Genel rapor altyapısındaki kullanıcı tarafından doldurulabilir `prepared_by` alanı korunmuştur.
- Uygulama durum çubuğuna ve Hakkında diyaloğuna `designed by S.Esim & gpt` imzası eklendi.
- Uygulama sürümü `0.16.9.4.15` olarak güncellendi; proje şeması `0.16.4`, kurulum/geometri model revizyonu ve uygulama kablo veri tabanı revizyonu `0.16.9.4.14` olarak korundu.
- `synthetic_20km_project_report.latest` çıktıları JSON, Markdown, HTML, DOCX ve PDF formatlarında üretici üzerinden yeniden oluşturuldu.

## Doğrulama

- Hesap modülleri: v0.16.9.4.14 ile byte düzeyinde aynı.
- Veri modeli modülleri: v0.16.9.4.14 ile byte düzeyinde aynı.
- Sentetik rapor proje imzası, hesap bölümleri, zorunlu uyarılar, rapor durumu ve seçili modüller değişmedi.
- Kaynak testleri: 352/352 PASS.
- DOCX: 11 sayfa render edilerek incelendi.
- PDF: 10 sayfa render edilerek incelendi.
- Kaldırılan kimlik ve eski demo atıfları için bağımsız paket taraması: 0 eşleşme.
