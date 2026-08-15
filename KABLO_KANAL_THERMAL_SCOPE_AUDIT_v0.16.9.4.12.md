# Kablo-Kanal çok devreli 2D termal kapsam denetimi

**Sürüm:** DiTuS Kablo Analizör v0.16.9.4.12  
**Proje şeması:** 0.16.4  
**Ana amaç:** Aynı kanal içindeki bütün fiziksel devreleri 2D termal alana taşımak; birlikte ve devre-bazlı izole çözümleri aynı geometri üzerinde karşılaştırmak.

## 1. Bulunan hata

v0.16.9.4.11 üretim bağı kanal katmanlarını ve gerçek `x-y` koordinatlarını 2D nodal motora taşıyordu. Ancak `solve_nodal_region()` fiziksel kablo listesini elektrik senaryosundaki `active_circuit_count` ile kesiyordu. Örneğin aynı kesitte iki devre varken N-1 veya tek aktif devre senaryosunda ikinci devrenin üç kablosu:

- sıcaklık alanından,
- malzeme rasterinden,
- çizimden,
- kablo sonuç tablosundan

tamamen kaldırılıyordu.

Bu davranış elektriksel olarak enerjisiz bir devrenin fiziksel gövdesinin de yok olduğu anlamına geliyordu ve ortak kanal fiziğini doğru temsil etmiyordu.

## 2. Düzeltilen model sınırı

Yeni kural iki ayrı kavramı ayırır:

- **Fiziksel olarak mevcut devre:** Kanal kesitinde kablosu bulunan devredir; her zaman 2D malzeme modelinde yer alır.
- **Enerjili devre:** Seçilen senaryo/kapsamda elektriksel kayıp üreten devredir.

Dolayısıyla çözüm kapsamı kablo nesnelerini silmez. Yalnız per-kablo akım ve kayıp çarpanlarını belirler.

Pasif devre için:

- `I = 0 A`
- iletken kaybı `0 W/m`
- kılıf/zırh kaybı `0 W/m`
- dielektrik kayıp `0 W/m`
- kablo eşdeğer ısıl iletkenliği ve geometrik hacmi korunur.

## 3. Çözüm kapsamları

### 3.1 SCENARIO_COMBINED

Elektrik tasarım senaryosunun enerjili devre sayısını kullanır. Üretim sonucu ve transient/rapor zincirinin ana girdisi olarak kalır.

### 3.2 ALL_CIRCUITS_COMBINED

Çok devreli Kablo-Kanal bölgelerinde bütün fiziksel devreleri aynı anda enerjilendirir. Bu sonuç:

- komşu devre karşılıklı ısınmasını,
- ortak kanal sıcak noktasını,
- tam yüklü kanal ampacity sınırını

gösterir.

### 3.3 ISOLATED::<circuit_id>

Yalnız seçilen devre ısı üretir. Diğer devreler aynı fiziksel konumda pasif kalır. Böylece devrenin kanal içindeki tekil katkısı, geometriyi sökmeden belirlenir.

Kapsamlar aktif yük senaryosu için hesaplanır. Çok devreli fiziksel kesit içermeyen bölgeler izole etkileşim kapsamına eklenmez; bu nedenle farklı kesit yapılarına sahip güzergâhlarda yararlı bölgesel sonuçlar, başka bir legacy/tek-devre bölge nedeniyle bastırılmaz.

Ek kapsamlar uzaysal **termal karşılıklı etki** çalışmasıdır. Bölgesel `lambda1` ve IEC karşılaştırma değeri ana elektrik senaryosundan alınır. Farklı bir bonding/işletme senaryosunun indükleme kayıpları incelenecekse o elektrik senaryosu birleşik hesap akışında ayrıca kurulup çözülmelidir.

## 4. Akım dağılımı

Fiziksel kablo kayıpları şu kayıt sırasıyla türetilir:

1. Devre `load_current_a`
2. Devre `load_factor`
3. Faz başına paralel kablo paylaşımı
4. Fiziksel kablo `current_override_a`
5. Fiziksel kablo `load_factor`
6. Aktif elektrik senaryosunun referans kablo akımına normalizasyon

Bu yöntem, DESIGN/N-1 ölçeğini korurken devreler veya paralel kablolar arasındaki kullanıcı tanımlı asimetriyi kaybetmez.

## 5. Kanal detayının termal modele girişi

Aşağıdaki Kablo-Kanal girdileri 2D nodal modelin doğrudan girdileridir:

- bütün fiziksel kabloların `x_m`, `depth_m` koordinatları,
- kablo dış çapı,
- hendek merkezi, alt genişliği, derinliği ve şevi,
- yataklama/kum zarfı,
- termal backfill,
- seçilmiş ve genel dolgu,
- yüzey tabakası,
- malzeme ısıl özdirençleri ve anizotropi,
- duct bank/grout ölçüleri,
- tüm aktif duct slotlarının merkezi ve iç/dış çapı,
- boş duct slotlarındaki iç dolgu/hava,
- koruma plakası,
- kullanıcı malzeme polygonları,
- yeraltı su seviyesi,
- dış doğrusal ısı kaynakları.

Çözülen malzeme sınırlarının asıl otoritesi `material_ids` rasteridir. Grafik üzerindeki hendek/katman/duct çizgileri, aynı üretim girdilerinden üretilen denetim bindirmesidir.

## 6. Sayısal iki-devre regresyonu

Simetrik iki TREFOIL devre, her devrede 800 A/kablo, devre merkez aralığı 0,45 m ve aynı kanal geometrisi:

| Kapsam | Enerjili/fiziksel devre | Kablo sayısı | Tmax [°C] | 2D ampacity [A/kablo] | Toplam Q [W/m] |
|---|---:|---:|---:|---:|---:|
| Senaryo birlikte | 1/2 | 6 | 47,2505 | 1291,3360 | 34,8354 |
| Kanalın tüm devreleri birlikte | 2/2 | 6 | 58,2050 | 1073,7206 | 72,2248 |
| Yalnız Devre 1 | 1/2 | 6 | 47,2505 | 1291,3360 | 34,8354 |
| Yalnız Devre 2 | 1/2 | 6 | 47,1794 | 1293,2502 | 34,8275 |

Devre 1 izole çözümüne göre iki devrenin birlikte enerjilenmesi:

- `ΔT = +10,9544 °C`
- `ΔIamp = -217,6154 A/kablo`

Bu fark kullanıcı arayüzünde `Karşılıklı devre etkisi` olarak gösterilir.

## 7. Duct boş-slot doğrulaması

2×3 duct bank içinde yalnız ilk üç slot doluyken, boş bir slot merkezine en yakın nodal hücre `MAT-AIR-01` olarak doğrulanmıştır. Böylece boş borular grout/toprak olarak yutulmaz; duct cidarı ve iç ortamı fiziksel modelde kalır.

DUCT_BANK eşdeğer analitik faz aralığı da A-B ve B-C komşu slot aralığının ortalaması olarak düzeltilmiştir. Önceki üç uzaklık geometrik ortalaması, düz slot sırasını yapay olarak büyütüyor ve hendek genişliği doğrulamasında her genişlik için sahte eksiklik üretebiliyordu.

## 8. Üretim güvenliği

- Ana IEC 60287, bonding/CIM, arıza/EPR, SVL ve transient denklemleri değiştirilmedi.
- Ek izole/tam-kanal kapsamları `circuit_scope_scenarios` alanında tutulur.
- Mevcut entegrasyonlar ve üretim durumu `scenarios` içindeki birincil `SCENARIO_COMBINED` sonucunu kullanmaya devam eder.
- Rapor veya sonuç görüntüleme proje girdisini değiştirmez.
- Kablo-Kanal kaydı sonuçları geçersiz kılar ve kullanıcıdan yeniden hesap ister.

## 9. Test kanıtı

- Toplam test: **346/346 PASS**
- Yeni özel testler:
  - birlikte ve iki izole kapsamın üretilmesi,
  - bütün kapsamlarda altı fiziksel kablonun korunması,
  - pasif devrede sıfır elektriksel kayıp,
  - birlikte çözümün izole çözüme göre daha yüksek sıcaklık vermesi,
  - boş duct slotunun hava malzemesi olarak rasterize edilmesi,
  - kapsam seçicisi ve kanal geometri bindirmesi UI sözleşmesi.
