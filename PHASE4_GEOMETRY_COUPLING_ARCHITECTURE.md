# FAZ 4 — Geometri bağlaşımı ve derinlik

## Tek doğruluk kaynağı
Kabul edilmiş `InstallationCrossSectionData` içindeki aktif `PhysicalCableData` kayıtları üretim geometri otoritesidir. Faz etiketli gerçek `x_m/depth_m`, devre/paralel kimliği, kablo dış çapı, duct-slot ilişkileri ve malzeme bölgeleri aynı snapshot/fingerprint içinde taşınır. Skaler spacing/arrangement alanları yalnız cache veya legacy fallback'tir.

## Derinlik sözleşmesi
Zemin yüzeyi `depth=0`, aşağı yön pozitiftir. IEC analitik gömme derinliği tek kabloda kablo eksenine, trefoil'de formasyon merkezine göredir. DiTuS trefoil gruplarında kanonik skaler gömme derinliğini üç faz eksen derinliğinin merkezinden türetir; explicit x-y kullanan motorlar her fazın gerçek koordinatını tüketir. `trench_depth_m` analitik image T4'e bağımsız terim olarak girmez; nodal/katman geometrisini tanımlar.

## Ortogonal yöntem-otoritesi modeli
Birleşik eski indirgeme sınıfları kaldırılmıştır. Üç eksen ayrı tutulur:
- `geometry_basis`: `PHYSICAL_ACCEPTED`, `TEMPLATE_DERIVED`, `LEGACY_SCALAR`;
- `material_field_class`: `HOMOGENEOUS`, `LAYERED`, `COMPLEX_REGIONS` (yeraltı suyu ayrıca reason-code ile izlenir);
- analitik `result_authority`: `IEC_ANALYTIC`, `ENGINEERING_APPROXIMATION`, `DERIVED_FROM_SCALAR`.

Bunlara ek olarak `authoritative_method` ve `analytical_preview_allowed` hesap yürütme politikasını taşır. Katmanlı/karma fiziksel kesitte analitik preview hesaplanmaya ve shadow karşılaştırmasına devam eder; üretim otoritesi nodal'dır. Legacy skaler geometri `DERIVED_FROM_SCALAR` yetkisini geçemez.

## Yüzey/mixed-zone preview
Mixed-zone eşdeğer yarıçap ve yüzey düzeltmesi hızlı engineering-preview'dur; IEC'nin jenerik çok-katmanlı normatif çözümü olarak etiketlenmez. Negatif yüzey düzeltmesi muhafazakâr olarak sıfıra kırpılır; ham değer ve clamp bayrağı ayrı evidence olarak tutulur. Kullanılmayan `far_field_effective_rho_km_w` üretim projeksiyonundan/persistence'tan kaldırılmıştır.

## Reason-code ayrımı
Katmanlı/karma geometri yetki indirimi ERROR değildir; analitik kolu öldürmeyen WARNING/evidence'dır. Yeraltı suyu sınırı `ANALYTIC_GROUNDWATER_BOUNDARY_REQUIRES_NODAL`, karma bölge `ANALYTIC_COMPLEX_REGIONS_REQUIRES_NODAL`, katmanlı alan `ANALYTIC_LAYERED_GEOMETRY_REQUIRES_NODAL` kodlarıyla ayrılır.

## Bonding ve route coupling
Bonding ve termal motorlar aynı resolved geometry snapshot'ını tüketir. Tek rastgele bölgeden spacing seçilmez; route contribution'ları kendi geometri ve uzunluklarıyla entegre edilir. CUSTOM koordinatlar primitive/global ağa doğrudan gider.
