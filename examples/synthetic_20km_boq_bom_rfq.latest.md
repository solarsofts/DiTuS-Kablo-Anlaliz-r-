# Sentetik 20 km Katalog Uygulama Örneği - BOQ/BOM/RFQ Paketi

- Proje kodu: `DITUS-DEMO-20KM-APPLIED`
- Üretim: `2026-08-06T23:38:51`
- Proje imzası: `290863e183b85ac7089d2e6cea5cedcf8e474f88f0f8489bb43f70ff4414d441`
- Durum: **CONDITIONAL_PROJECT_DATA**

## Özet

| Gösterge | Değer |
|---|---:|
| Net yeraltı güzergâhı | 20000.000 m |
| Montajlı tek damarlı kablo | 121740.000 m |
| Sipariş tek damarlı kablo | 124175.000 m |
| Termination | 12 adet |
| Joint | 120 adet |
| Cross-bonding link box | 28 adet |
| Grounding link box | 12 adet |
| Toplam link box | 40 adet |
| SVL seti | 28 set |
| SVL elemanı/polü | 84 adet |
| Makara | 126 adet |
| Makara planı | VALID |
| Sipariş/fire payı | 2423.000 m |
| Toplam aşım | 0.000 m |

## BOQ / BOM

| Kalem | Kategori | Tanım | Otomatik miktar | Nihai miktar | Birim | Durum | Dayanak |
|---|---|---|---:|---:|---|---|---|
| CBL-001 | CABLE | Tek damarlı OG güç kablosu | 124175.000 | 124175.000 | m | CONDITIONAL_PROJECT_DATA | route × 3 faz × devre × paralel + termination/joint kuyrukları + montaj + fire + yedek |
| ACC-TERM-001 | CABLE_ACCESSORY | Tek damarlı kablo terminasyonu | 12.000 | 12.000 | adet | CONDITIONAL_PROJECT_DATA | TERMINATION nodes × 3 faz × devre × paralel + yedek |
| ACC-JOINT-001 | CABLE_ACCESSORY | Tek damarlı sectionalizing / straight joint | 120.000 | 120.000 | adet | CONDITIONAL_PROJECT_DATA | SECTIONALIZING_JOINT nodes × 3 faz × devre × paralel + yedek |
| BND-LB-CROSS-001 | BONDING_AND_SVL | Cross-bonding link box | 28.000 | 28.000 | adet | CONFIRMED_PROJECT_DATA | minor cross boundaries × circuit count |
| BND-LB-GROUND-001 | BONDING_AND_SVL | Major-section grounding link box | 12.000 | 12.000 | adet | CONFIRMED_PROJECT_DATA | major-section grounded boundaries × circuit count |
| BND-SVL-001 | BONDING_AND_SVL | Metalik kılıf gerilim sınırlayıcı (SVL) elemanı/polü | 84.000 | 84.000 | adet | CONDITIONAL_PROJECT_DATA | cross-bonding boundary × 3 pole × circuit + explicit spare poles |
| BND-SVL-SET-001 | BONDING_AND_SVL | Üç fazlı SVL seti | 28.000 | 28.000 | set | CONDITIONAL_PROJECT_DATA | cross-bonding link-box count |
| BND-LEAD-001 | BONDING_AND_SVL | Bonding bağlantı iletkeni / koaksiyel bonding kablosu | 396.000 | 396.000 | m | CONDITIONAL_PROJECT_DATA | Σ(lead length × 3 faz × devre) + açık bonding lead payı |
| GND-POINT-001 | GROUNDING | Bonding/terminasyon topraklama bağlantı noktası | 16.000 | 16.000 | nokta | CONDITIONAL_PROJECT_DATA | grounded nodes × circuit count |
| SUP-CLEAT-001 | MARKING_AND_SUPPORT | Üç faz kablo kelepçe/cleat seti | 40008.000 | 40008.000 | set | CONDITIONAL_PROJECT_DATA | Σ(ceil(section/spacing)+1) × circuits × parallel |
| MRK-TAPE-001 | MARKING_AND_SUPPORT | Yeraltı kablo ikaz bandı | 21000.000 | 21000.000 | m | ENGINEERING_ASSUMPTION | route length + warning tape allowance |
| MRK-TAG-001 | MARKING_AND_SUPPORT | Kablo güzergâh ve aksesuar işaretleme seti | 26.000 | 26.000 | set | ENGINEERING_ASSUMPTION | route sections + accessory points |
| CIV-EXC-001 | CIVIL_WORKS | Kablo hendeği kazısı | 48400.000 | 48400.000 | m³ | ENGINEERING_ASSUMPTION | Σ(trench_width × trench_depth × region_length) |
| CIV-TBF-001 | CIVIL_WORKS | Termal dolgu malzemesi | 5350.000 | 5350.000 | m³ | ENGINEERING_ASSUMPTION | Σ(width × (bedding + cover) × length) |
| CIV-DUCT-001 | CIVIL_WORKS | Kablo koruma borusu / duct | 30000.000 | 30000.000 | m | CONDITIONAL_PROJECT_DATA | region_length × phases × circuits × cables/phase |

## RFQ Teknik Gereksinimleri

### CBL-001 - Tek damarlı OG güç kablosu

20.3/35 (40.5) kV; SINGLE_CORE_XLPE; Al 400 mm²; metalik ekran/kılıf 35 mm²; XLPE; dış çap 56.5786 mm; Rdc20 0.0778 Ω/km

Miktar: **124175.000 m**

İstenen belgeler:
- Üretici teknik veri föyü ve konstrüksiyon çizimi
- Rutin test sertifikaları
- Tip test raporları / standart uygunluk beyanı
- Makara boyu, makara ölçüsü ve net/brüt ağırlık
- Metalik ekran tel yapısı ve kısa devre dayanımı

### ACC-TERM-001 - Tek damarlı kablo terminasyonu

20.3/35 (40.5) kV; 400 mm² Al; iç/dış ortam ve tesis arayüzü proje uçlarına göre teyit edilecektir.

Miktar: **12.000 adet**

İstenen belgeler:
- Tip test raporu
- Montaj talimatı
- Kablo uyumluluk çizelgesi
- Saha test gereksinimleri

### ACC-JOINT-001 - Tek damarlı sectionalizing / straight joint

20.3/35 (40.5) kV; 400 mm²; metalik ekran/kılıf ayrımı ve bonding çıkışları proje şemasına uygun.

Miktar: **120.000 adet**

İstenen belgeler:
- Tip test raporu
- Montaj talimatı
- Ekran ayırma ve bonding bağlantı çizimi
- Joint bay minimum ölçüleri

### BND-LB-CROSS-001 - Cross-bonding link box

CROSS_BONDED; üç faz çapraz bağlantı baraları ve SVL bağlantı noktaları; erişilebilirlik/IP sınıfı saha koşuluna göre.

Miktar: **28.000 adet**

İstenen belgeler:
- İç çapraz bağlantı şeması
- Muhafaza/IP ve korozyon sınıfı
- Kısa devre akım dayanımı
- Kablo gland/terminal detayları

### BND-LB-GROUND-001 - Major-section grounding link box

Üç faz metalik kılıfın solid-ground bağlantısı; SVL içermez; çıkarılabilir test linkleri ve topraklama barası.

Miktar: **12.000 adet**

İstenen belgeler:
- Solid-ground iç bağlantı şeması
- Topraklama barası kısa devre dayanımı
- Muhafaza/IP ve korozyon sınıfı

### BND-SVL-001 - Metalik kılıf gerilim sınırlayıcı (SVL) elemanı/polü

Bağlantı STAR_GROUNDED; sürekli gerilim marjı %10; nihai MCOV/TOV/residual/enerji sınıfı üretici eğrileri ve hesap sonucu ile seçilecektir.

Miktar: **84.000 adet**

İstenen belgeler:
- MCOV/TOV eğrileri
- Residual gerilim eğrileri
- Enerji dayanım verileri
- Rutin test sertifikası
- Montaj ve topraklama talimatı

### BND-SVL-SET-001 - Üç fazlı SVL seti

Bir cross-bonding link box için üç bağımsız SVL koruma kolu.

Miktar: **28.000 set**

### BND-LEAD-001 - Bonding bağlantı iletkeni / koaksiyel bonding kablosu

Tip: COAXIAL; olabildiğince kısa güzergâh; kesit, ekranlama, darbe ve kısa devre dayanımı üretici/hesap ile doğrulanacaktır.

Miktar: **396.000 m**

### GND-POINT-001 - Bonding/terminasyon topraklama bağlantı noktası

Topraklama iletkeni, bağlantı barası, pabuç ve korozyon koruması dahil; hedef direnç ve EPR kriteri topraklama tasarımından.

Miktar: **16.000 nokta**

### SUP-CLEAT-001 - Üç faz kablo kelepçe/cleat seti

Trefoil; azami aralık 1 m; kısa devre elektrodinamik dayanımı arıza hesabına göre belgelenecektir.

Miktar: **40008.000 set**

İstenen belgeler:
- Kısa devre dinamik test/hesap raporu
- Kablo dış çapı uyumluluğu
- Montaj aralığı ve tork talimatı

### MRK-TAPE-001 - Yeraltı kablo ikaz bandı

Güzergâh boyunca sürekli, dayanıklı ve proje dilinde işaretli; yatay bant sayısı tip kesite göre teyit edilecektir.

Miktar: **21000.000 m**

### MRK-TAG-001 - Kablo güzergâh ve aksesuar işaretleme seti

Terminasyon, joint, link box ve güzergâh dönüş/erişim noktaları için UV/korozyon dayanımlı etiketleme.

Miktar: **26.000 set**

### CIV-EXC-001 - Kablo hendeği kazısı

Termal bölge kesit genişliği × hendek derinliği × bölge uzunluğu; şev, kabarma ve nakliye katsayıları hariç.

Miktar: **48400.000 m³**

### CIV-TBF-001 - Termal dolgu malzemesi

Bedding + kablo üstü termal dolgu hacmi; sıkışma/kabarma ve satın alma yoğunluğu ayrıca teklif şartında belirtilecektir.

Miktar: **5350.000 m³**

### CIV-DUCT-001 - Kablo koruma borusu / duct

İç/dış çap ve malzeme ilgili termal kesit şablonundan; her tek damarlı kablo için ayrı duct.

Miktar: **30000.000 m**

## Makara Planı

| Makara | Kesim | Fire/pay | Yedek | Toplam | Azami | Bakiye | Kalan | Aşım | Kesimler | Durum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| DRM-001 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C1-PA-G1-S1:969m | VALID |
| DRM-002 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C1-PA-G1-S21:969m | VALID |
| DRM-003 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C1-PB-G1-S1:969m | VALID |
| DRM-004 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C1-PB-G1-S21:969m | VALID |
| DRM-005 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C1-PC-G1-S1:969m | VALID |
| DRM-006 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C1-PC-G1-S21:969m | VALID |
| DRM-007 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S1:969m | VALID |
| DRM-008 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S21:969m | VALID |
| DRM-009 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S1:969m | VALID |
| DRM-010 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S21:969m | VALID |
| DRM-011 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S1:969m | VALID |
| DRM-012 | 969.0 m | 16.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S21:969m | VALID |
| DRM-013 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S2:966m | VALID |
| DRM-014 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S3:966m | VALID |
| DRM-015 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S4:966m | VALID |
| DRM-016 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S5:966m | VALID |
| DRM-017 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S6:966m | VALID |
| DRM-018 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S7:966m | VALID |
| DRM-019 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S8:966m | VALID |
| DRM-020 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S9:966m | VALID |
| DRM-021 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S10:966m | VALID |
| DRM-022 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S11:966m | VALID |
| DRM-023 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S12:966m | VALID |
| DRM-024 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S13:966m | VALID |
| DRM-025 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S14:966m | VALID |
| DRM-026 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S15:966m | VALID |
| DRM-027 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S16:966m | VALID |
| DRM-028 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S17:966m | VALID |
| DRM-029 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S18:966m | VALID |
| DRM-030 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S19:966m | VALID |
| DRM-031 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PA-G1-S20:966m | VALID |
| DRM-032 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S2:966m | VALID |
| DRM-033 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S3:966m | VALID |
| DRM-034 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S4:966m | VALID |
| DRM-035 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S5:966m | VALID |
| DRM-036 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S6:966m | VALID |
| DRM-037 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S7:966m | VALID |
| DRM-038 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S8:966m | VALID |
| DRM-039 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S9:966m | VALID |
| DRM-040 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S10:966m | VALID |
| DRM-041 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S11:966m | VALID |
| DRM-042 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S12:966m | VALID |
| DRM-043 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S13:966m | VALID |
| DRM-044 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S14:966m | VALID |
| DRM-045 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S15:966m | VALID |
| DRM-046 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S16:966m | VALID |
| DRM-047 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S17:966m | VALID |
| DRM-048 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S18:966m | VALID |
| DRM-049 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S19:966m | VALID |
| DRM-050 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PB-G1-S20:966m | VALID |
| DRM-051 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S2:966m | VALID |
| DRM-052 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S3:966m | VALID |
| DRM-053 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S4:966m | VALID |
| DRM-054 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S5:966m | VALID |
| DRM-055 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S6:966m | VALID |
| DRM-056 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S7:966m | VALID |
| DRM-057 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S8:966m | VALID |
| DRM-058 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S9:966m | VALID |
| DRM-059 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S10:966m | VALID |
| DRM-060 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S11:966m | VALID |
| DRM-061 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S12:966m | VALID |
| DRM-062 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S13:966m | VALID |
| DRM-063 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S14:966m | VALID |
| DRM-064 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S15:966m | VALID |
| DRM-065 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S16:966m | VALID |
| DRM-066 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S17:966m | VALID |
| DRM-067 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S18:966m | VALID |
| DRM-068 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S19:966m | VALID |
| DRM-069 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C1-PC-G1-S20:966m | VALID |
| DRM-070 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S2:966m | VALID |
| DRM-071 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S3:966m | VALID |
| DRM-072 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S4:966m | VALID |
| DRM-073 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S5:966m | VALID |
| DRM-074 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S6:966m | VALID |
| DRM-075 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S7:966m | VALID |
| DRM-076 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S8:966m | VALID |
| DRM-077 | 966.0 m | 20.0 m | 0.0 m | 986.0 m | 1000.0 m | 14.0 m | 14.0 m | 0.0 m | CUT-C2-PA-G1-S9:966m | VALID |
| DRM-078 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S10:966m | VALID |
| DRM-079 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S11:966m | VALID |
| DRM-080 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S12:966m | VALID |
| DRM-081 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S13:966m | VALID |
| DRM-082 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S14:966m | VALID |
| DRM-083 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S15:966m | VALID |
| DRM-084 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S16:966m | VALID |
| DRM-085 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S17:966m | VALID |
| DRM-086 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S18:966m | VALID |
| DRM-087 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S19:966m | VALID |
| DRM-088 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PA-G1-S20:966m | VALID |
| DRM-089 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S2:966m | VALID |
| DRM-090 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S3:966m | VALID |
| DRM-091 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S4:966m | VALID |
| DRM-092 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S5:966m | VALID |
| DRM-093 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S6:966m | VALID |
| DRM-094 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S7:966m | VALID |
| DRM-095 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S8:966m | VALID |
| DRM-096 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S9:966m | VALID |
| DRM-097 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S10:966m | VALID |
| DRM-098 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S11:966m | VALID |
| DRM-099 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S12:966m | VALID |
| DRM-100 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S13:966m | VALID |
| DRM-101 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S14:966m | VALID |
| DRM-102 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S15:966m | VALID |
| DRM-103 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S16:966m | VALID |
| DRM-104 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S17:966m | VALID |
| DRM-105 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S18:966m | VALID |
| DRM-106 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S19:966m | VALID |
| DRM-107 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PB-G1-S20:966m | VALID |
| DRM-108 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S2:966m | VALID |
| DRM-109 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S3:966m | VALID |
| DRM-110 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S4:966m | VALID |
| DRM-111 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S5:966m | VALID |
| DRM-112 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S6:966m | VALID |
| DRM-113 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S7:966m | VALID |
| DRM-114 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S8:966m | VALID |
| DRM-115 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S9:966m | VALID |
| DRM-116 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S10:966m | VALID |
| DRM-117 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S11:966m | VALID |
| DRM-118 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S12:966m | VALID |
| DRM-119 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S13:966m | VALID |
| DRM-120 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S14:966m | VALID |
| DRM-121 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S15:966m | VALID |
| DRM-122 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S16:966m | VALID |
| DRM-123 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S17:966m | VALID |
| DRM-124 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S18:966m | VALID |
| DRM-125 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S19:966m | VALID |
| DRM-126 | 966.0 m | 19.0 m | 0.0 m | 985.0 m | 1000.0 m | 15.0 m | 15.0 m | 0.0 m | CUT-C2-PC-G1-S20:966m | VALID |

## Varsayımlar

- Devre sayısı: 2; paralel kablo/faz: 1; tek damarlı iletken yolu sayısı: 6.
- Montaj payı %1; fire %2; yedek kablo %0.
- Terminasyon kuyruğu 5 m/uç; joint kuyruğu 2 m/taraf.
- Makara azami boyu 1000 m (Katalog kaydı SYN-MFR-A-MV40K5-AL400-35); kesim yuvarlaması 1 m.
- Joint/termination miktarları tek damarlı aksesuar adedidir; link box miktarı üç fazlı kutu adedidir; SVL miktarı tek fazlı eleman adedidir.
- BOQ/BOM miktarları maliyet veya satın alma onayı değildir; teknik teklif, üretici uyumluluğu ve saha metrajı ayrıca kontrol edilmelidir.

## Uyarılar

- Kablo verisi VERIFIED değildir; BOQ/BOM/RFQ teknik tanımı koşullu proje verisi içerir.
- SVL adedi bonding grafiğinden üretildi; üretici/model ve MCOV/TOV/enerji sınıfı nihai seçilmemiştir.
- Kazı ve termal dolgu miktarları DESIGN termal kesitlerinden türetilmiştir; saha/as-built metrajı değildir.
