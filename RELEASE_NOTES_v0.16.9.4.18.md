# DiTuS Kablo Analizör v0.16.9.4.18 — FAZ 3.1 Kritik Çalışma Zamanı Hataları

## 20 °C altı çalışma

- IEC 60287 iletken direnç düzeltmesindeki yapay 20 °C alt sınırı kaldırıldı; 0 °C için yeni sınır konmadı.
- Sert hata yalnız sonlu olmayan sıcaklık, mutlak sıfır altı, pozitif olmayan düzeltme katsayısı veya pozitif olmayan direnç gibi fiziksel/matematiksel geçersizliklerde oluşur.
- Soğuk sıcaklık düzeltmesi `thermal_trace` içinde katsayı ve kaynakla izlenir; warning/notes üretmez ve kaydı koşullu yapmaz.
- IEC termal çekirdeği sıfır tasarım akımını geçerli çalışma noktası olarak kabul eder.

## Malzeme α/ρ çözümü

- Cu, Al, Pb/kurşun ve bronz için ortak malzeme ρ20/α20 resolver'ı kullanılır.
- Al kayıtlarında tarihsel Cu varsayılanı `0.00393` otomatik olarak Al malzeme profiline göç eder.
- Göç yalnız `PROJECT_CABLE_SNAPSHOT` ve `GENERIC_TEMPLATE` otomatik legacy kaynaklarıyla sınırlıdır; `MANUAL_OVERRIDE` kayıtları korunur.
- `LEGACY_SCHEMA_ALPHA_DEFAULT` geçici uyumluluk sabiti açıkça adlandırıldı ve emeklilik koşulu belgelendi.

## Güzergâh hata izolasyonu

- Üretim yolu `solve_thermal_route()` artık senaryo × bölüm sonuç matrisi üretir.
- Proje-geneli hatalar fail-fast; bölüm-özgü bilinen mühendislik hataları ilgili hücrede toplanır.
- `solve_thermal_route()` ile termal ön işlemcinin kullandığı materialization aynı doğrulama sınıflandırmasını paylaşır.
- Sonuçlar `COMPLETE/PARTIAL/FAILED` tamamlanma ekseni ile `UYGUN/UYGUN_DEGIL/INDETERMINATE` uygunluk eksenini ayrı taşır.
- Kısmi çözüm resmi hat ampacity'si üretmez. Ampacity üst sınırı ve sıcaklık alt sınırı yalnız tanısal/monoton kanıt olarak raporlanır.
- Fiziksel ret kapıları, eksik bölümler olsa da kesin yetersizlik gösterebilir; veri hükmü kablonun DRAFT/CONDITIONAL/VERIFIED durumu ile birlikte sunulur.
- Tek bir başarısız bölüm artık hayatta kalan bölümler üzerinden yanlış `UYGUN` oluşturamaz.

## Senaryolar ve tüketiciler

- Eşit akımlı NORMAL/N-1/DESIGN çalışma noktaları tek çözümde birleştirilir; kapsanan kimlikler alias olarak korunur.
- Sıfır yükte yalnız bir `DESIGN — 0 A` çalışma noktası oluşur.
- Ana pencere, rapor/özet, termal ayrıntı, grafik ve optimizasyon tüketicileri yeni durumları açıkça işler.
- `FAILED` çalışma `_fail_engine_run`, `PARTIAL` çalışma koşullu sonuç yoluna bağlanır.
- Nodal/transient boş koleksiyonları artık vacuous truth ile yanlış `UYGUN` üretemez.

## Yeniden üretilen sentetik veri

- Al α20 düzeltmesi nedeniyle sentetik katalog uygulama snapshot'ı `SNAP-5CC2714CF472` olarak yenilendi.
- Sentetik proje, katalog seçim/karşılaştırma, uygulama, regresyon, tedarik ve rapor çıktıları yeniden üretildi.
- Proje şeması `0.16.4` olarak korunur.

## Ertelenenler

- VERTICAL/DUCT analitik yerleşim desteği: FAZ 3.2.
- Bonding kılıf sıcaklığı 20 °C alt kapısı ve sıfır akım bonding yolu: FAZ 6.6.
