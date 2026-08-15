# DiTuS Kablo Analizör v0.16.9.4.10
## Kablo-Kanal Düzeni — hesap bağlaşımı denetimi

## 1. Sonuç hükmü

Kablo-Kanal Düzeni yalnız görsel bir çizim değildir. Kaydedilen fiziksel kablo `x_m/depth_m` koordinatları ve kullanıcı tarafından kabul edilmiş kanal geometrisi, ayrı **SHADOW_COMPARE** N-iletken EM, gerçek x-y termal ve elektro-termal kapalı çevrim motorlarına gerçekten girer.

Ancak ana üretim sonuçları olan klasik IEC 60287 güzergâh hesabı, klasik bonding/CIM, ana 2D nodal, IEC 60853 transient, Arıza/EPR, SVL ve BOQ miktar hesabı hâlâ `installation_design` yerine eski `thermal_design` şablonları, `route_sections` ve bonding skalerlerini kullanır. Bu nedenle Kablo-Kanal ekranında yapılan değişiklikler ana üretim sonuçlarını otomatik değiştirmez.

**Mühendislik hükmü:** Ekran işlevsiz değildir; fiziksel gölge doğrulama katmanında etkindir. Fakat üretim hesabına terfi etmemiştir. Kullanıcıya gösterilen `solver_coupling_mode=DESIGN_ONLY` durumu doğrudur.

## 2. TREFOIL düzeltmesi

- TREFOIL üç tek damarlı kablonun temas eden üçgen demeti olarak tanımlandı.
- Üç fazın bütün karşılıklı merkez uzaklıkları gerçek kablo dış çapına eşittir.
- Kullanıcının faz merkez aralığı girdisi TREFOIL için tamamen yok sayılır.
- Ortak yerleşim panelinde faz aralığı alanı TREFOIL seçiliyken gizlenir.
- Devre Yerleşimi tablosunda TREFOIL satırının faz aralığı hücresi dış çapa ayarlanır ve düzenlemeye kapatılır.
- FLAT ve VERTICAL için kullanıcı faz merkez aralığı korunur.
- Paralel trefoil grupları ve farklı devreler arasındaki merkez aralıkları bağımsız olarak korunur.
- Temas eden kablolar artık termal matriste “çakışma” sayılmaz; yalnız gerçek zarf penetrasyonu reddedilir.

## 3. Gerçekten kullanılan Kablo-Kanal girdileri

### 3.1 N-iletken EM gölge motoru

Kaynak zinciri:

`InstallationCrossSectionData.physical_cables` → `multiconductor_em._build_primitives()` → `primitive_impedance_matrix_ohm_km()` → yerel/global N-core ve N-sheath çözümü.

Gerçekten kullanılanlar:

- Her fiziksel kablonun x koordinatı ve derinliği
- Devre, faz ve paralel grup kimliği
- Faz sırası ve devre yük akımı
- Fiziksel kablo aktif/pasif durumu
- Akım override ve açı override
- Kesit–güzergâh/minor-section eşleşmesi

Etkilediği çıktılar:

- Karşılıklı endüktif bağlaşım
- Kılıf indüklenen gerilimi ve akımı
- Paralel core akım paylaşımı
- Core ve kılıf metal kayıpları
- Global bonding ağı ve elektro-termal iterasyon girdileri

Sınır:

- AC direnç içindeki proximity bileşeni henüz tam gerçek N-kablo x-y integralinden üretilmiyor; mevcut fiziksel parametre/route faz aralığı kapsamı korunuyor.

### 3.2 Gerçek x-y termal gölge motoru

Kaynak zinciri:

`installation_design` → `solve_multiconductor_thermal()` → `_channel_profile_and_overrides()` → gerçek x-y analitik termal matris + `_NodalModel(explicit_locations=...)`.

Gerçekten kullanılanlar:

- Fiziksel kablo x-y koordinatları
- Hendek genişliği ve derinliği
- Hendek merkezi ve yan şev oranı
- Yataklama kalınlığı
- Termal backfill yüksekliği
- Seçilmiş/genel dolgu ve yüzey tabakası kalınlıkları
- Doğal zemin, yataklama, termal backfill, seçilmiş dolgu, genel dolgu ve yüzey malzemeleri
- Duct bank genişliği/yüksekliği ve grout malzemesi
- Duct iç/dış çapı
- Koruma plakası ölçü ve malzemesi
- Beton kanal/tünel eşdeğer geometrisi
- Kullanıcı özel malzeme polygonları
- Harici çizgisel ısı kaynakları

Dolaylı kullanılanlar:

- Alt/üst kum örtüsü ve yan kum payı, `synchronise_direct_buried_geometry()` ile gerçek kablo zarfından `bedding_thickness_m`, hendek genişliği ve kablo derinliklerine dönüştürülür.

Aktivasyon koşulu:

- `channel_geometry.source_reference` boş, `LEGACY_*` veya `MIGRATED_*` ise eski projelerin sayısal eşitliği için kanal geometrisi gölge termale aktarılmaz.
- Kullanıcı düzenlemesi sonrasında kaynak `USER_INTERACTIVE_GEOMETRY` olur ve geometri etkinleşir.

### 3.3 Elektro-termal kapalı çevrim gölge motoru

`solve_electrothermal_coupled()` her dış iterasyonda:

1. Gerçek x-y global N-core/N-sheath EM çözümünü,
2. Gerçek x-y kanal termal çözümünü,
3. Sıcaklığa bağlı core/kılıf/GCC dirençlerini

birlikte tekrar çözer. Sonuç proje λ1 değerini veya ana üretim sonuçlarını yazmaz; gölge doğrulama sonucudur.

## 4. Ana üretim hesaplarına girmeyen Kablo-Kanal girdileri

### 4.1 IEC 60287 güzergâh hesabı

`solve_thermal_route()` ve `resolve_thermal_region()` yalnız `thermal_design.templates`, bölge override değerleri ve route verisini kullanır. `installation_design` okunmaz.

Sonuç olarak Kablo-Kanal ekranındaki:

- gerçek x-y yerleşim,
- kullanıcı hendek genişliği/derinliği,
- kum örtüleri,
- özel malzeme polygonları,
- duct slotları

ana IEC 60287 ampacity/T4 sonucunu doğrudan değiştirmez.

### 4.2 Ana 2D nodal hesap

`solve_nodal_route()` → `solve_nodal_region()` yolu, kablo konumlarını `_expanded_cable_locations()` ile termal şablonun arrangement/phase spacing/circuit spacing değerlerinden yeniden üretir. Kablo-Kanal fiziksel kesiti okunmaz.

### 4.3 IEC 60853 transient

Transient çözüm ana nodal sonucu üzerinden ilerler; Kablo-Kanal `installation_design` verisini doğrudan kullanmaz.

### 4.4 Klasik bonding/CIM

Klasik bonding ve primitive CIM yolları `route_sections.phase_spacing_m` ve bonding skalerlerini kullanır. Gerçek Kablo-Kanal x-y geometrisini kullanan çözüm ayrı “Genel N-İletken EM Gölge Çözümü”dür.

### 4.5 Arıza/EPR ve SVL

Bu motorlarda `installation_design` okuması yoktur. Kanal geometrisi sonuçlara doğrudan girmez.

### 4.6 BOQ/BOM/RFQ

Kazı ve dolgu miktarları `thermal_design` bölge/şablonlarının `trench_width_m`, `trench_depth_m` ve `bedding_thickness_m` değerlerinden hesaplanır. Kablo-Kanal ekranındaki gerçek kanal geometrisi BOQ’ya aktarılmamıştır.

## 5. Sayısal denetim örneği

Aynı varsayılan proje üzerinde yalnız Kablo-Kanal geometri kaynağı kullanıcı kabulüne çevrilip hendek/backfill ölçüleri değiştirildi:

- Gerçek x-y termal gölge maksimum iletken sıcaklığı: **71.185765 °C → 62.626333 °C**
- Ana üretim 2D nodal maksimum iletken sıcaklığı: **77.555716 °C → 77.555716 °C**

Bu deney iki sınırı birlikte kanıtlar:

1. Kanal geometrisi gölge termal motorda gerçekten işlev görür.
2. Aynı geometri ana nodal üretim yoluna henüz bağlı değildir.

Regresyon testi: `tests/test_cable_channel_calculation_coupling_v0169410.py`.

## 6. Gölge model içindeki kalan sınırlamalar

- Duct bank grout bloğu eşdeğer dikdörtgen bölge olarak çözülür.
- Duct halkaları aktif fiziksel kablo merkezlerinde oluşturulur; bütün aktif ductlar için ilk slotun iç/dış çapı ortak kabul edilir. Farklı çaplı slotların aynı kesitte ayrı çözümü yoktur.
- Boş/yedek duct slotları termal alanda ayrı halka olarak çözülmez.
- Beton kanal ve tünel iç ortamı eşdeğer iletim bölgesidir; doğal/zorlanmış taşınım ve radyasyon çözülmez.
- Warning mesh, warning tape ve işaretleme elemanları termal/EM hesap girdisi değildir; kesit/uygulama ve miktarlandırma nesneleridir.
- Gerçek x-y proximity kaybı tam genelleştirilmemiştir.

## 7. Önerilen sonraki geliştirme kapısı

Üretim hesaplarına doğrudan geçiş tek adımda yapılmamalıdır. Önerilen sıra:

1. `installation_design` → üretim termal profil adaptörü oluşturulmalı.
2. Aynı bölge için legacy şablon ve fiziksel kanal sonuçları yan yana çalıştırılmalı.
3. Genişlik, derinlik, malzeme, x-y ve duct değişim duyarlılık testleri eklenmeli.
4. IEC 60287 analitik sonuç, gerçek x-y 2D nodal sonuç ve kapalı çevrim sonuç için kabul zarfı tanımlanmalı.
5. BOQ kazı/dolgu miktarları aynı fiziksel geometriden türetilmeli.
6. Ancak bu kapılar geçtikten sonra `DESIGN_ONLY` yerine kontrollü üretim bağlaşımı açılmalı.

Bu sürümde ana mimari terfi yapılmadı; yalnız TREFOIL fiziksel doğruluğu ve temas kabulü düzeltildi, mevcut bağlaşım sınırı test ve dokümantasyonla kesinleştirildi.
