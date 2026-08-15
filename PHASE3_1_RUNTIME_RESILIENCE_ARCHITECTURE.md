# FAZ 3.1 — IEC Termal Çalışma Zamanı Dayanıklılığı

## Kapsam

Bu faz iki çalışma zamanı güvenlik problemini kapatır: 20 °C altındaki iletken sıcaklıklarının yapay giriş hatasına dönüşmesi ve senaryo/bölüm çözümünde tek bir yerel hatanın bütün güzergâh sonucunu silmesi.

## Sıcaklığa bağlı direnç

- 20 °C yalnız `R20` referans sıcaklığıdır; alt hesap sınırı değildir.
- `Rθ = R20 · [1 + α20(θ-20)]` bağıntısı mutlak sıfır, sonluluk ve pozitif direnç kapılarıyla uygulanır.
- 0 °C için yeni yapay sınır konmaz.
- 20 °C altı düzeltme uyarı veya `CONDITIONAL` nedeni değildir; yalnız `thermal_trace` içinde kaynak ve katsayıyla izlenir.
- IEC termal çalışma noktası için `I = 0` geçerlidir.

## Malzeme katsayısı ve legacy göçü

- Ortak malzeme resolver'ı Cu, Al, Pb/kurşun ve bronz için ρ20 ve α20 değerlerini tanır.
- Açık kullanıcı override'ı malzeme varsayılanından üstündür.
- `LEGACY_SCHEMA_ALPHA_DEFAULT = 0.00393`, alan bazlı kaynak bağı bulunmayan eski `CableData` kayıtlarını ayırt etmek için geçici uyumluluk sabitidir.
- Al kabloda otomatik eski `0.00393` değeri açık override sayılmaz; etkin değer malzeme profilinden çözülür.
- Göç yalnız otomatik legacy kaynak türleri `PROJECT_CABLE_SNAPSHOT` ve `GENERIC_TEMPLATE` için uygulanır. `MANUAL_OVERRIDE` ve alan bazlı gerçek kaynak kayıtları korunur.
- Legacy sabiti, `CableData.parameter_sources` ile α alanı arasında güvenilir alan bazlı bağ kurulduğunda kaldırılacaktır.

## Senaryo × bölüm sonuç sözleşmesi

Her çalışma hücresi başarı veya yapılandırılmış hata sonucu üretir. Sonuçlar özgün senaryo ve bölüm sırasını korur.

Tamamlanma ekseni:

- `COMPLETE`
- `PARTIAL`
- `FAILED`

Mühendislik uygunluğu ekseni:

- `UYGUN`
- `UYGUN_DEGIL`
- `INDETERMINATE`

Kısmi senaryoda resmi güzergâh ampacity'si veya resmi maksimum sıcaklık üretilmez. Çözülen bölgelerden yalnız:

- `ampacity_upper_bound_a`
- `temperature_lower_bound_c`

üretilir. Bu sınırlar veya fiziksel ret kapıları yetersizliği kesin gösteriyorsa `PARTIAL + UYGUN_DEGIL`; aksi hâlde `PARTIAL + INDETERMINATE` kullanılır.

`delta_theta <= 0`, `numerator <= 0` ve `denominator <= 0` kapıları kaldırılmaz; girdilere göre kararlı durum çözümünün bulunmadığını gösteren fiziksel ret nedenleridir. Hüküm, kablonun `DRAFT/CONDITIONAL/VERIFIED` veri durumuyla birlikte taşınır.

## Doğrulama ve materialization

`solve_thermal_route()` ve `materialize_route_sections_partial()` aynı doğrulama sınıflandırmasını kullanır:

- proje-geneli hatalar fail-fast,
- bölüm-özgü hatalar ilgili hücreye kaydedilir,
- diğer bölümler çözülmeye devam eder,
- beklenmeyen programlama istisnaları gizlenmez.

Termal ön işlemci de aynı kısmi materialization sonucunu kullanır.

## Senaryo tekilleştirme

Aynı sayısal akıma sahip çalışma noktası bir kez çözülür. Kimlik önceliği `DESIGN > N_MINUS_ONE > NORMAL` olur; eşdeğer kimlikler alias olarak izde korunur. Bütün yükler sıfırsa tek `DESIGN — 0 A` çalışma noktası üretilir.

## Kapsam dışı kayıtlar

- Bonding metalik kılıf sıcaklığındaki 20 °C kapısı FAZ 6.6'ya bırakılmıştır. `sheath_operating_temperature_c` termal çözümden türetilmediği için soğuk projede IEC yolu çalışırken bonding yolunun düşmesi ayrıca kapatılacaktır.
- Nodal ve transient motorların gelecekte kısmi sonuç üretmesi hâlindeki tam matris sözleşmesi bu fazın dışındadır; boş koleksiyonun yanlış `UYGUN` vermesi engellenmiştir.
- VERTICAL/DUCT analitik yerleşim kapsamı FAZ 3.2'dir.
