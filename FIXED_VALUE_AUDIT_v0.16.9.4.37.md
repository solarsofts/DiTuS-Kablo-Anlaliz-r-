# DiTuS v0.16.9.4.37 — Sabit Değer / Katsayı Yönetişimi Denetimi

## Amaç

Bu denetim, v0.16.9.4.34 → v0.16.9.4.35 değişikliğinde sabit sayıların hangi kapsamda kaldırıldığını ve v0.16.9.4.37'de hangi sınıfların kodda kalması gerektiğini kaydeder.

## Sonuç

v0.16.9.4.35 hesap/model dizinlerinde toplu bir "sabit değer temizliği" yapmamıştır. Sayısal davranışı değiştiren tek fizik dosyası `cable_physical_parameters.py` olmuş; burada desteklenen Milliken konstrüksiyonlarının `ks/kp` çiftleri otomatik resolver'dan kaldırılmıştır. Diğer temel fizik, malzeme ve denklem sabitleri kodda kalmıştır.

v0.16.9.4.37 aşağıdaki yönetişimi uygular:

1. **Temel fizik/matematik sabitleri — KODDA KALIR.** Örnek: `epsilon_0`, `mu0/(2*pi)`, dairesel iletken GMR katsayısı ve birim dönüşümleri.
2. **Standart denklem katsayıları — KODDA KALIR.** Skin/proximity ve diğer kapalı-form denklemlerin sayısal katsayıları kullanıcı girdisi değildir.
3. **Desteklenen konstrüksiyona ait küçük skaler standart katsayı çiftleri — resolver içinde KALIR.** `ks/kp` değerleri, konstrüksiyon sınıfı açıkça biliniyorsa otomatik çözülür; Cu Milliken profili bilinmiyorsa tahmin edilmez. Açık ve izlenebilir kullanıcı/üretici `ks/kp` çifti otomatik resolver'ın önüne geçer.
4. **Proje/saha/malzeme verileri — evrensel sabit DEĞİLDİR.** Zemin ısıl özdirenci, ortam sıcaklığı, gömme derinliği, gerçek kablo `Rdc`, `tan delta`, `epsilon_r` vb. aktif proje/kablo/veri tabanından gelir. İsteğe bağlı kullanıcı profili bu verilerin yerine geçmez ve eksikliği motoru bloklamaz.
5. **DiTuS sayısal/politika eşikleri — açıkça politika olarak tutulur.** Yakınsama toleransları, mesh sınırları, UI zoom katsayıları vb. standart sabiti diye sunulmaz.
6. **Sentetik/demo başlangıç değerleri — tasarım otoritesi değildir.** Proje şablonlarındaki başlangıç değerleri yalnız örnek/başlangıç verisidir ve provenance/authority kapılarını aşamaz.

## v0.16.9.4.35'te bulunan regresyon

`StandardDefaults` ekranındaki proje/site/malzeme alanları global hesap önkoşulu yapılmıştı. Bu değerler hesap motorları tarafından doğrudan tüketilmediği halde eksik olmaları bütün motorları durdurabiliyordu. Bu global kapı v0.16.9.4.37'de kaldırılmıştır. Hesap önkontrolü tekrar aktif proje/kablo verisine dayanır.

## Konstrüksiyon katsayısı kuralı

- Yuvarlak masif, yuvarlak çok telli ve açıkça tanımlanmış desteklenen Milliken yapılarında resolver kullanılır.
- Cu Milliken tel profili bilinmiyorsa `MILLIKEN_PROFILE_REQUIRED` ile fail-closed.
- Desteklenmeyen/özel konstrüksiyonda doğrulanmış açık `ks/kp` çifti gerekir.
- Bir `ks/kp` çiftinin 1,0 olması "skin/proximity etkisi sıfırdır" anlamına gelmez; bu değerler `xs/xp` formüllerinin konstrüksiyon katsayılarıdır.

## Telif / dağıtım notu

DiTuS standart sayfası, tablo düzeni, açıklama metni veya şekli dağıtmaz. Kod, hesap denkleminin çalışması için gerekli skaler değerleri ve kaynak kimliğini kullanır. Standart yayıncılarının telif/lisans koşulları ayrıca geçerlidir; kamuya açık dağıtım için `STANDARDS_NOTICE` ve gerekli izin değerlendirmesi FAZ 8'in parçasıdır.
