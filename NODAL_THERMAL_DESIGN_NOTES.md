# v0.12.1 2D Nodal Termal Tasarım ve Sonuç Denetimi Notları

## Çözüm tipi

Solver, kablo eksenine dik 2D kesitte kararlı durum ısı iletimini hücre-merkezli sonlu hacim yöntemiyle çözer:

```text
−∇·(k∇T) = q
```

Her hücre için komşu hücrelerle yüzey iletkenliği harmonik ortalamayla kurulur. Sistem seyrek matris olarak çözülür.

## Koordinat sistemi

- `x`: yatay konum
- `y`: yüzeyden aşağı pozitif derinlik
- Model birim kablo uzunluğu için çözülür.
- Isı kaynakları `W/m`, hücre yüzey iletkenlikleri `W/(m·K)` biçimindedir.

## Mesh üretimi

Ağ, temel kaba grid ile aşağıdaki yerel kenarların birleşiminden oluşturulur:

- Kablo merkezleri çevresindeki ince grid
- Hendek sağ/sol sınırları
- Bedding, dolgu ve yüzey katmanı sınırları
- Duct bank sınırları
- Duct ve kablo dış çapları
- Yeraltı suyu seviyesi

Çok küçük hücrelerin kötü koşullu matris üretmesini engellemek için birbirine çok yakın kenarlar birleştirilir.

## Malzeme iletkenliği

Ana girdi termal özdirençtir:

```text
k = 1 / ρth
```

Anizotropi oranı tanımlanmışsa:

```text
kx = k·√a
ky = k/√a
```

Yeraltı suyu seviyesinin altında uygun zemin/dolgu kategorilerinde kullanıcı tanımlı iletkenlik çarpanı uygulanır. Bu, akışkan hareketi çözmeyen açık bir eşdeğer yaklaşımdır.

## Geometri önceliği

Hücre malzemesi şu sırayla belirlenir:

1. Doğal zemin
2. Hendek ve dolgu katmanları
3. Duct-bank/grout alanı
4. Duct iç boşluğu ve duct duvarı
5. Yüzey katmanı
6. Kablo hücreleri

Kablo hücreleri yüksek eşdeğer iletkenlikle izotermale yakın tutulur. Kablo içindeki gerçek katman sıcaklık düşümü 2D hücrelere bırakılmaz; IEC tabanlı T1–T3 iç termal zinciriyle hesaplanır.

## Sınır koşulları

- Üst yüzey: sabit sıcaklık veya seri iletim+konveksiyon direnci
- Yan sınırlar: sabit derin zemin sıcaklığı
- Alt sınır: sabit derin zemin sıcaklığı

Kablolar derinleştikçe uzak alt sınırın yapay soğutma yaratmaması için model derinliği otomatik genişletilir. Yatay sınırlar da kablo kümesine ve gömülme derinliğine göre genişletilir.

## Isı kaynaklarının dağıtılması

Her fiziksel kablonun toplam kaybı, kablo dairesi içinde kalan hücrelere hücre alanı oranında dağıtılır:

```text
Qtotal = Qconductor + Qsheath + Qarmour + Qdielectric
```

Mesh kaba olsa bile her kabloya en az bir kaynak hücresi atanır.

## Elektriksel–termal iterasyon

Her iterasyonda:

1. Önceki iletken sıcaklığında `Rac(T)` hesaplanır.
2. İletken, sheath, armour ve dielektrik kayıpları oluşturulur.
3. 2D dış sıcaklık alanı çözülür.
4. Kablo hücrelerinden jacket sıcaklığı bulunur.
5. T1–T3 iç termal zinciriyle iletken sıcaklığı hesaplanır.
6. Sıcaklık farkı tolerans altına inene kadar sönümlü iterasyon yapılır.

Metalik kılıf kaybı:

```text
Qsheath = λ1,region · Qconductor
```

olarak güncellenir. `λ1,region`, mevcutsa primitive bonding çözümünden chainage bazında gelir.

## Ampacity araması

İlk üst sınır IEC ampacity, tasarım akımı ve minimum başlangıç değerinden oluşturulur. Sıcaklık sınırı aşılana kadar üst sınır büyütülür, sonra bisection uygulanır.

Kritik sıcaklık, kesitteki bütün aktif kabloların maksimum iletken sıcaklığıdır.

## Enerji dengesi

Çözüm sonrasında bütün sabit/konvektif sınırlardan çıkan ısı toplanır:

```text
εenergy = |Qboundary − Qsource| / Qsource
```

Ayrıca seyrek lineer sistem için maksimum mutlak residual raporlanır.

## IEC 60287 karşılaştırması

Her bölge için hem analitik IEC ampacity hem 2D ampacity saklanır:

```text
ΔI% = (I2D − IIEC) / IIEC · 100
```

Farkın küçük olması zorunlu kabul edilmez. Duct, grout, yüzey katmanı, çoklu devre ve sonlu dolgu geometrileri analitik eşdeğerden anlamlı biçimde ayrılabilir. Büyük fark, veri ve mesh gözden geçirme tetikleyicisidir.

## Mesh yakınsama testi

Aynı bölge ve akım:

- kaba mesh ölçeği
- inceltilmiş mesh ölçeği

ile iki kez çözülür. Maksimum iletken sıcaklığı farkı ve hücre sayıları raporlanır. Bu kontrol otomatik kabul garantisi değil, sayısal duyarlılık göstergesidir.

## 2D modelin fiziksel sınırı

Model enine kesitte sonsuz/uzun sabit geometri varsayar. Aşağıdakiler 3D gerektirir:

- HDD giriş ve çıkışı
- Duct-bank başlangıç/bitişi
- Joint bay ve menhol
- Farklı kesitlerin kısa mesafede geçişi
- Kablo kesişimi
- Eksenel sıcaklık taşınımının önemli olduğu yerel bölgeler


## v0.12.1 sonuç denetimi hotfix'i

Sıcaklık alanı tek raster olarak çizilir; yalancı hücre-seam çizgileri kaldırılmıştır. Malzeme sınırı, mesh, hendek/su geometrisi, kablolar, sıcak nokta ve yaklaşık izotermler bağımsız katmanlardır. Bölge/senaryo seçimi, karşılaştırma tablosu ve sonuç denetçisi aynı sayısal sonuç kaydını kullanır.
