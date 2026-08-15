# v0.16.6 Gerçek x-y Çoklu Kablo Termal Motoru — Teknik Notlar

## 1. Amaç

Bu kapı, fiziksel elektromanyetik ağın ürettiği kablo bazlı kayıpları gerçek kurulum geometrisine taşır. Eski termal motorların yaptığı otomatik trefoil/flat konum üretimi yeni gölge yolda kullanılmaz.

## 2. Girdi zinciri

```text
Global N-core + N-kılıf çözümü
        ↓
Ic(kablo), Ish(kablo, minor section)
        ↓
Termal bölge ↔ fiziksel kesit eşlemesi
        ↓
Wc, Wsh, Wd, Warm [W/m]
        ↓
Gerçek x-y analitik matris + ortak 2D alan
```

Her fiziksel yolun anahtarı:

```text
Devre : Faz : Paralel No
```

Güzergâh kesitleri değişse dahi aynı elektriksel yol bu anahtarla izlenir.

## 3. Bölgesel kılıf kaybı

Bir termal bölge bir veya daha fazla minor section ile kesişebilir. Kabloya ait bölgesel kılıf kayıp yoğunluğu:

\[
W_{sh,i,r}=\frac{1}{L_{cov}}
\sum_s L_{r\cap s}\frac{P_{sh,i,s}}{L_s}
\]

Burada:

- `r`: termal bölge,
- `s`: minor section,
- `Lr∩s`: zincirleme örtüşme uzunluğu,
- `Psh,i,s`: fiziksel kılıfın section toplam I²R kaybı.

## 4. Kablo kayıpları

Core akımı global sistemden sabit alınır. Termal iterasyonda iletken direnci sıcaklığa göre güncellenir:

\[
W_{c,i}=|I_{c,i}|^2R_{ac,i}(T_i)
\]

\[
W_{sh,i}=\text{global bonding ağından bölgesel sonuç}
\]

\[
W_{d,i}=2\pi f C U_0^2\tan\delta
\]

Geçici zırh gölge kaynağı:

\[
W_{arm,i}=\lambda_2 W_{c,i}
\]

Toplam:

\[
W_i=W_{c,i}+W_{sh,i}+W_{d,i}+W_{arm,i}
\]

## 5. Analitik gerçek x-y çözüm

Her fiziksel kablo merkezi `(xi, hi)` olarak alınır.

Self terim:

\[
R_{ii}=\frac{\rho}{2\pi}\operatorname{acosh}\left(\frac{h_i}{r}\right)
\]

Mutual terim:

\[
R_{ij}=\frac{\rho}{2\pi}\ln\left(\frac{D_{image,ij}}{D_{actual,ij}}\right)
\]

Sıcaklık artışı:

\[
\Delta\mathbf T_j=\mathbf R_{th}\mathbf W+\Delta\mathbf T_{external}
\]

Analitik mixed-zone seçeneğinde dolgu bölgesi eşdeğer yarıçap düzeltmesiyle temsil edilir. Bu, dikdörtgen trench/backfill geometrisinin yerine geçmez.

## 6. 2D sonlu-hacim çözümü

Çözülen denklem:

\[
-\nabla\cdot(k\nabla T)=q
\]

Her fiziksel kablo ayrı dairesel kaynak maskesine sahiptir. Kablo bazlı farklı `Wi` değerleri kendi gerçek koordinatından alana verilir. Malzeme katmanları mevcut termal şablondan; kablo konumları fiziksel kurulum modelinden gelir.

Harici kaynaklar `(x, depth, W/m)` ile en yakın hücreye uygulanır. Enerji kapanışı toplam kablo ve harici kaynak gücünü kapsar.

## 7. İç termal sıcaklık artışı

Tek damarlı kablo için explicit kayıp yolu:

\[
\Delta T_{int}=
W_cT_1+0.5W_dT_1+
(W_c+W_{sh}+W_d)T_2+
(W_c+W_{sh}+W_{arm}+W_d)T_3
\]

Bu ifade `Wsh=lambda1·Wc` ve `Warm=lambda2·Wc` olduğunda mevcut IEC lambda biçimine eşdeğerdir; yeni motor gerçek ayrı kılıf kaybını kullanır.

## 8. İterasyon

1. Başlangıç kablo sıcaklıkları atanır.
2. `Rac(T)` ve `Wc` güncellenir.
3. Kablo bazlı toplam ısı kaynakları kurulur.
4. 2D alan çözülür.
5. Jacket sıcaklığı ve iç termal artıştan conductor sıcaklığı bulunur.
6. Under-relaxation uygulanır.
7. Maksimum sıcaklık farkı toleransın altına inene kadar tekrarlanır.

Bu kapıda `Ic` ve `Ish` yeniden çözülmez. Tam elektro-termal kapalı çevrim v0.16.7 hedefidir.

## 9. Standart ve doğrulama çerçevesi

- IEC 60287-1-3: paralel tek damarlı kablolarda faz akımı paylaşımı ve dolaşım kayıpları
- IEC 60287-2-1: kararlı durum termal direnç kapsamı
- CIGRE TB 797: sheath-bonding sistemi tasarım ve modelleme mimarisi
- CIGRE TB 880: kablo rating hesap araçlarının doğrulama vakaları

Bu sürüm bu kaynakların tüm benchmarklarını tamamladığı iddiasında değildir. Motor `SHADOW_COMPARE` kalır.

## 10. Sonraki teknik müdahale

v0.16.7’de sıcaklık geri beslemesi elektromanyetik sisteme bağlanacaktır:

```text
T → Rac/Rsh → global Ic/Ish → Wc/Wsh → 2D T → yakınsama
```
