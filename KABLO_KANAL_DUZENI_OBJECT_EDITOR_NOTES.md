# v0.16.9.1 — Kablo-Kanal Düzeni Nesne Editörü Teknik Notları

## 1. Geometri tanımı

Kesit koordinatı metre cinsindendir; `x` yatay, `depth` zemin yüzeyinden aşağı pozitiftir.

Hendek taban yarı genişliği:

```text
b_bottom = trench_width_m / 2
```

Her derinlikte yarı genişlik:

```text
b(y) = b_bottom + side_slope_h_to_v × (trench_depth_m - y)
```

Bu nedenle üst genişlik:

```text
W_top = trench_width_m + 2 × side_slope_h_to_v × trench_depth_m
```

`side_slope_h_to_v = 0` eski dik duvarlı modeli birebir korur.

## 2. Kullanıcı malzeme polygonları

`ThermalMaterialRegionData.vertices_m`, sıralı `[x_m, depth_m]` çiftlerinden oluşur. En az üç nokta ve sıfırdan büyük alan zorunludur.

2D ağda hücre merkezi polygon içinde kalıyorsa bölgenin malzemesi atanır. Kullanıcı bölgeleri `priority` artan sırada uygulanır; daha yüksek öncelik önceki kullanıcı bölgesini geçersiz kılar.

Fiziksel kurulum elemanları kullanıcı polygonlarından sonra uygulanır. Böylece özel zemin/kaya bölgesi duct duvarını, grout bankını, beton kanalı veya koruma plakasını yanlışlıkla değiştiremez.

## 3. Duct ve kablo snap politikası

Kablo, aktif duct merkezine iç çap ve kablo yarıçapından türetilen tolerans içinde yaklaştırılırsa:

```text
duct_slot_id = slot.slot_id
cable.x = slot.x
cable.depth = slot.depth
```

Duct taşındığında ona atanmış kablolar aynı merkeze taşınır. Kablo slottan uzağa sürüklenirse slot ataması temizlenir.

## 4. Shadow bağlantısı

Özel kesit bilgileri yalnız `channel_geometry.source_reference` kullanıcı tarafından kabul edilmiş durumda ise `multiconductor_thermal` üzerinden nodal modele gönderilir.

Yeni override girdileri:

```text
trench_side_slope_h_to_v
custom_material_regions
```

Legacy veya migrate edilmiş varsayılan kesitler eski termal profilini korur.

## 5. Doğrulama kodları

- `CHANNEL_SIDE_SLOPE`
- `DUPLICATE_MATERIAL_REGION`
- `MATERIAL_REGION_GEOMETRY`
- `UNKNOWN_THERMAL_MATERIAL`
- mevcut `CABLE_OUTSIDE_CHANNEL`, gerçek trapez sınırını kullanır.

## 6. Sonraki kapı

- Polygon köşe tutamaçları ve köşe ekle/sil,
- katman/polygon boolean kesişim ön izlemesi,
- termal kontur ve malzeme-ID overlay,
- construction dimension seti ve kesit çıktısı,
- kanal içi konveksiyon/radyasyon alt modeli.
