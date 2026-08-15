# v0.12 Termal Güzergâh ve Bölge Tasarım Notları

## Veri mimarisi

```text
ThermalDesignData
 ├─ ThermalMaterialData[]
 ├─ ThermalCrossSectionTemplate[]
 └─ ThermalRegion[]
```

`ThermalRegion`, route üzerinde `[start_m, end_m]` aralığı, şablon kimliği, geçiş tipi, veri katmanı, kaynak ve yerel override sözlüğü taşır. Hesap sırasında şablon ve override değerleri birleştirilerek değişmez `EffectiveThermalProfile` oluşturulur.

## Bölgesel tanımlama ilkesi

Tek bir proje zemin değeri kullanılmaz. Güzergâh boyunca değişen:

- doğal zemin,
- termal dolgu,
- yüzey kaplaması,
- yeraltı suyu,
- kurulum tipi,
- gömülme derinliği,
- faz/devre aralığı

chainage bazında ayrı bölgelerde tanımlanır.

Kullanıcı her metreyi tek tek tanımlamaz. Tip kesit şablonu bir veya daha fazla aralığa atanır; yalnız yerel farklılıklar override edilir.

## Malzeme kaynağı ve güven

Malzeme kaydı şu alanları ayrı tutar:

- Isıl özdirenç / iletkenlik
- Kuru/yaş yoğunluk
- Nem
- Hacimsel ısı kapasitesi
- Kompaksiyon
- Kritik kuruma ve kuru-durum ısıl özdirenci
- Anizotropi
- `DESIGN / TESTED / AS_BUILT`
- Kaynak tipi, rapor referansı ve güven seviyesi

Kararlı durum analitik ve 2D çözümde seçilmiş ısıl özdirenç kullanılır. Isı kapasitesi ve zaman bağımlı nem alanları IEC 60853/transient katmanı için saklanır.

## Bölge kapsama kuralları

Etkin bölgeler güzergâhı 0 m’den toplam uzunluğa kadar boşluksuz ve çakışmasız kapsamalıdır. Tolerans `coverage_tolerance_m` ile tanımlanır. Hata bulunan model hesaplanmaz.

## Analitik ve 2D çift çözüm

Her bölge iki katmanla değerlendirilebilir:

1. IEC 60287 / `AUTO_MIXED_ZONE` analitik ön çözüm
2. 2D sonlu hacim sıcaklık alanı ve ampacity

Analitik sonuç hızlı tarama ve karşılaştırma için korunur. 2D çözüm, gerçek malzeme bölgelerini ve çoklu kablo termal etkileşimini kullanır.

## Bölgesel λ1

Primitive bonding sonucu varsa her primitive minor section metalik kılıf kaybı, termal bölgeyle örtüşen uzunluk oranında dağıtılır:

```text
λ1_region = P_sheath,region / P_conductor,region
```

Primitive sonuç yoksa bonding/global `λ1` kullanılır. 2D iterasyonda metalik kılıf kaybı iletken kaybındaki sıcaklık değişimiyle birlikte yeniden ölçeklenir.

## Kritik bölge

Her yük senaryosunda hem IEC hem 2D hat kapasitesi ayrı belirlenir:

```text
I_route,IEC = min(I_IEC,region)
I_route,2D  = min(I_2D,region)
```

Kritik bölge için kabloyu tüm hat boyunca büyütmek yerine bölgesel dolgu, derinlik, aralık, duct/grout ve yerel farklı kesit alternatifleri değerlendirilebilir.

## Kademeli geçişler

`GRADUAL` kaydı veri modelinde korunur. Mevcut IEC ve 2D çözüm her bölgeyi sabit enine kesit olarak çözer. Kademeli geçişte eksenel ısı akışı, gelecekteki yerel 3D modelin kapsamıdır.
