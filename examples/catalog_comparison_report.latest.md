# DiTuS Kablo Katalog Teknik Karşılaştırma Raporu

- Proje: **Sentetik 20 km Çift Devre Yeraltı Kablo Hattı** (DITUS-DEMO-20KM)
- Sistem: **34.5 kV**
- Tasarım akımı: **386.574 A/devre**
- Üretim: `2026-08-06T23:38:03`

> Bu rapor katalog verilerini, kaynak izlenebilirliğini ve hesap hazırlığını karşılaştırır. Nihai kablo uygunluk onayı değildir.

## Aday özeti

| Sıra | Üretici / model | Kablo/faz | Iref aritmetik | Iref normalize | Norm. marj | Ref. durumu | Fizik model | ΔV | Veri | Kapılar | Doğrulama hükmü |
|---:|---|---:|---:|---:|---:|---|---|---:|---|---|---|
| 1 | Üretici A / Sentetik Al 1x400/35 | 1 | 545.0 A | — | — | REFERENCE_ONLY_INCOMPLETE | NOT_AVAILABLE | %4.39190 | CONDITIONAL | CONDITIONAL_READY | REFERENCE_NORMALIZATION_REQUIRED |
| 2 | Üretici B / Sentetik Al 1x400/35 | 1 | 571.0 A | — | — | REFERENCE_ONLY_INCOMPLETE | NOT_AVAILABLE | %4.26533 | CONDITIONAL | CONDITIONAL_READY | REFERENCE_NORMALIZATION_REQUIRED |
| 3 | Üretici C / Sentetik Cu 1x400/35 | 1 | 680.0 A | — | — | REFERENCE_ONLY_INCOMPLETE | NOT_AVAILABLE | %3.18001 | CONDITIONAL | CONDITIONAL_READY | REFERENCE_NORMALIZATION_REQUIRED |

## Katalog parametre matrisi

| Parametre | Birim | Üretici A | Üretici B | Üretici C |
|---|---|---|---|---|
| İletken Rdc @20 °C | Ω/km | 0.0778 | 0.0754 | 0.047 |
| İletken Rdc @90 °C | Ω/km | — | — | — |
| Endüktans — üçgen demet | mH/km | 0.4 | 0.39 | 0.38 |
| Endüktans — düz tertip | mH/km | 0.46 | 0.45 | 0.44 |
| Kapasitans | µF/km | 0.244587 | 0.244587 | 0.244587 |
| Katalog ampacity — toprak/üçgen | A | 545 | 571 | 680 |
| Katalog ampacity — toprak/düz | A | 558 | 584 | 695 |
| Kablo dış çapı | mm | 57.71 | 56.013 | 57.144 |
| Net ağırlık | kg/km | 3624.5 | 3348.3 | 6046.4 |

## 1. Üretici A — Sentetik Al 1x400/35

- Kaynak seviyesi: `SYNTHETIC_DEMO`
- Kaynak sayfası: Sentetik satır A
- Referans koşulu: toprakta üçgen demet; toprak 20°C; derinlik 0.7 m; ρth 1 K·m/W; katalog yük faktörü 1; Tamamen sentetik karşılaştırma koşulu; düzeltme faktörü içermez.
- Referans normalizasyonu: `REFERENCE_ONLY_INCOMPLETE`; kritik bölge `—`
- Aritmetik Iref toplamı: 545.000 A (uygunluk rating'i değildir)
- Normalize katalog benchmarkı: —
- Fiziksel model karşılaştırması: `NOT_AVAILABLE`
- Katalog skaler kapsamı: 8 mevcut / 1 eksik
- Bloke eksik: 0; üretici teyidi: 2; varsayım: 3

### Eksik/koşullu veriler
- Gerçek iletken çapı
- Metalik ekran/kılıf kesiti
- Metalik ekran tel adedi ve tel çapı
- Katman ısıl özdirençleri
- Katman hacimsel ısı kapasiteleri

### Uyarılar
- Konstrüksiyon/model verisi koşullu; üretici çizimi veya test verisi gerekiyor.
- Katalog Iref proje koşullarına kaynaklı faktörlerle normalize edilmedi; ham ×N değeri uygunluk kapısı değildir.
- RS-01 Sentetik standart hendek: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w
- RS-02 Sentetik yüksek termal özdirenç bölgesi: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w
- RS-03 Sentetik yol geçişi duct bank: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w, installation_method
- RS-04 Sentetik HDD geçişi: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w, installation_method

## 2. Üretici B — Sentetik Al 1x400/35

- Kaynak seviyesi: `SYNTHETIC_DEMO`
- Kaynak sayfası: Sentetik satır B
- Referans koşulu: toprakta üçgen demet; toprak 20°C; derinlik 0.7 m; ρth 1 K·m/W; katalog yük faktörü 1; Tamamen sentetik karşılaştırma koşulu; düzeltme faktörü içermez.
- Referans normalizasyonu: `REFERENCE_ONLY_INCOMPLETE`; kritik bölge `—`
- Aritmetik Iref toplamı: 571.000 A (uygunluk rating'i değildir)
- Normalize katalog benchmarkı: —
- Fiziksel model karşılaştırması: `NOT_AVAILABLE`
- Katalog skaler kapsamı: 8 mevcut / 1 eksik
- Bloke eksik: 0; üretici teyidi: 2; varsayım: 3

### Eksik/koşullu veriler
- Gerçek iletken çapı
- Metalik ekran/kılıf kesiti
- Metalik ekran tel adedi ve tel çapı
- Katman ısıl özdirençleri
- Katman hacimsel ısı kapasiteleri

### Uyarılar
- Konstrüksiyon/model verisi koşullu; üretici çizimi veya test verisi gerekiyor.
- Katalog Iref proje koşullarına kaynaklı faktörlerle normalize edilmedi; ham ×N değeri uygunluk kapısı değildir.
- RS-01 Sentetik standart hendek: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w
- RS-02 Sentetik yüksek termal özdirenç bölgesi: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w
- RS-03 Sentetik yol geçişi duct bank: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w, installation_method
- RS-04 Sentetik HDD geçişi: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w, installation_method

## 3. Üretici C — Sentetik Cu 1x400/35

- Kaynak seviyesi: `SYNTHETIC_DEMO`
- Kaynak sayfası: Sentetik satır C
- Referans koşulu: toprakta üçgen demet; toprak 20°C; derinlik 0.7 m; ρth 1 K·m/W; katalog yük faktörü 1; Tamamen sentetik karşılaştırma koşulu; düzeltme faktörü içermez.
- Referans normalizasyonu: `REFERENCE_ONLY_INCOMPLETE`; kritik bölge `—`
- Aritmetik Iref toplamı: 680.000 A (uygunluk rating'i değildir)
- Normalize katalog benchmarkı: —
- Fiziksel model karşılaştırması: `NOT_AVAILABLE`
- Katalog skaler kapsamı: 8 mevcut / 1 eksik
- Bloke eksik: 0; üretici teyidi: 2; varsayım: 3

### Eksik/koşullu veriler
- Gerçek iletken çapı
- Metalik ekran/kılıf kesiti
- Metalik ekran tel adedi ve tel çapı
- Katman ısıl özdirençleri
- Katman hacimsel ısı kapasiteleri

### Uyarılar
- Konstrüksiyon/model verisi koşullu; üretici çizimi veya test verisi gerekiyor.
- Katalog Iref proje koşullarına kaynaklı faktörlerle normalize edilmedi; ham ×N değeri uygunluk kapısı değildir.
- RS-01 Sentetik standart hendek: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w
- RS-02 Sentetik yüksek termal özdirenç bölgesi: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w
- RS-03 Sentetik yol geçişi duct bank: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w, installation_method
- RS-04 Sentetik HDD geçişi: eksik düzeltme -> soil_temperature_c, burial_depth_m, soil_thermal_resistivity_km_w, installation_method

## Hesap izi

- DiTuS v0.16.9.4.27 FAZ 6.8 katalog referans-normalizasyon ve fiziksel model karşılaştırma raporu. Katalog ampacity değerleri yalnız yayımlandıkları referans koşullar için benchmarktır; karşılaştırma sonucu nihai kablo uygunluk onayı değildir.
- DiTuS v0.16.9.4.27 FAZ 6.8 catalog reference-condition screening. Catalog current ratings are used only under their stated reference conditions; final design requires project IEC 60287, 2D thermal, bonding and fault validation.
- Sistem: 34.5 kV; normal 167.348 A/devre; N-1 334.696 A/devre; tasarım 386.574 A/devre.
- 6 katalog/parallel varyantı değerlendirildi.
- Katalog ampacity değerleri proje güzergâhı için doğrudan nihai rating kabul edilmedi.
- 3 farklı katalog kaydı/aday varyantı teknik karşılaştırmaya alındı.
- İlk sıra yalnız ileri doğrulama önceliğidir: Üretici A Sentetik Al 1x400/35; durum REFERENCE_NORMALIZATION_REQUIRED.
- Hiçbir aday 'nihai uygun' olarak etiketlenmedi.
