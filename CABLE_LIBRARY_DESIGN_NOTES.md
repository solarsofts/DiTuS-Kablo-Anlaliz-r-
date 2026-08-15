# Kablo Kütüphanesi ve Parametrik Konstrüksiyon — v0.14

## Ana karar

Elektriksel ve termal solverların kullandığı kablo verisi, katalog satırından doğrudan okunmaz. Proje içinde değişmez snapshot olarak saklanır.

## Veri modeli

```text
CableLibraryData
 ├─ CableCatalogRecord[]
 └─ CableParameterSource[]

CableCatalogRecord
 ├─ kimlik / üretici / seri / model
 ├─ gerilim sınıfı / iletken / kesit
 ├─ durum ve etiketler
 └─ cable_snapshot

CableData
 ├─ mevcut solver scalar alanları
 ├─ katalog/snapshot kimliği
 ├─ parametric layer stack
 ├─ source records
 └─ validation state
```

## Katman rolleri

- `CONDUCTOR`
- `CONDUCTOR_SCREEN`
- `INSULATION`
- `INSULATION_SCREEN`
- `WATER_BLOCKING`
- `METALLIC_SCREEN`
- `METALLIC_SHEATH`
- `BEDDING`
- `ARMOUR`
- `OUTER_SHEATH`

Yeni roller `OTHER` olarak saklanabilir; hesap motoruna etkisi açıkça bağlanmadan solver girdisi yapılmaz.

## Kaynak sınıfları

Katalog, üretici çizimi, test raporu, hesaplanan değer, standart türevi ve kullanıcı varsayımı ayrı tutulur. Kaynaklar arasında sessiz öncelik değiştirme yapılmaz.

## Snapshot politikası

- Snapshot SHA-256 canonical JSON üzerinden üretilir.
- Snapshot kimliği hash'in ilk 12 karakterinden türetilir.
- Katalog kaydı değişince proje snapshot'ı değişmez.
- Kablo değişince termal, bonding, arıza ve SVL sonuçları `STALE` yapılır.

## Hesap senkronizasyonu

Katman modelinden mevcut solver alanlarına aşağıdaki eşleştirme yapılır:

- conductor → `conductor_area_mm2`, `conductor_diameter_mm`, material
- insulation → `t1_outer_diameter_mm`, εr, tanδ
- metallic screen/sheath → `sheath_cross_section_mm2`, mean diameter, Rdc20
- outer layers → `t2_outer_diameter_mm`, `overall_diameter_mm`
- layer ρth → T1/T2/T3 effective material inputs

Kapasitans koaksiyel geometriden hesaplanan başlangıç değeridir. Üretici/test değeri girilmişse kullanıcı kaynak kaydıyla bunu koruyabilir.

## Doğrulama

### Error

- Katman iç/dış çapı geçersiz
- Katman çakışması
- İletken, izolasyon veya metalik ekran yok
- İletken/screen kesiti yok
- Tel geometrisi ile toplam ekran kesiti ciddi uyumsuz
- Kapasitans veya toplam dış çap üretilemiyor

### Warning

- Katmanlar arasında tanımsız boşluk
- Kaynak atanmamış veya kaynağı bulunamayan katman
- Ekran toplam kesiti var fakat tel sayısı/çapı bilinmiyor
- Kritik kaynak doğrulanmamış
- Permitivitе gibi bir değer için açık varsayım kullanılması

## Katalog paket formatı

```json
{
  "format": "DITUS_CABLE_CATALOG",
  "schema_version": "0.14",
  "package": {
    "records": [],
    "sources": []
  }
}
```

## Sonraki aşama

v0.15'te üretici katalogları doğrulanmış kayıt paketlerine dönüştürülecek. PDF otomatik okuma yalnız aday veri üretir; kullanıcı onayı, sayfa referansı ve doküman hash'i olmadan ana kayda alınmaz.
