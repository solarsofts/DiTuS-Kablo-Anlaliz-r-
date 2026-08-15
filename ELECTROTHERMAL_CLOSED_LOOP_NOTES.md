# v0.16.7 Elektro-Termal Kapalı Çevrim — Teknik Notlar

## 1. Amaç

Bu motor, genel N-core/N-kılıf elektromanyetik ağ ile gerçek x-y çoklu kablo termal alanını sıcaklık geri beslemesi altında birlikte çözer. Amaç tek seferlik kayıp aktarımı yerine sıcaklık, direnç, akım paylaşımı, kılıf akımı ve kayıpların birbiriyle tutarlı sabit noktasını bulmaktır.

Motor `SHADOW_COMPARE` durumundadır ve üretim sonuçlarını değiştirmez.

## 2. Durum değişkenleri

Her fiziksel kesit ve fiziksel kablo için iki sıcaklık durumu taşınır:

\[
T_{c,s,i}
\]

\[
T_{sh,s,i}
\]

Burada:

- `s`: fiziksel kesit,
- `i`: fiziksel kablo,
- `Tc`: iletken sıcaklığı,
- `Tsh`: metalik kılıf/screen sıcaklığıdır.

Başlangıç değerleri ilgili termal bölgelerin uzunluk ağırlıklı ortam sıcaklığından oluşturulur.

## 3. Sıcaklığa bağlı elektriksel parametreler

Her dış iterasyonda:

\[
R_{dc,i}(T)=R_{dc,20,i}\left[1+\alpha_i(T-20)\right]
\]

\[
R_{ac,i}(T)=R_{dc,i}(T)(1+y_{s,i}+y_{p,i})
\]

\[
R_{sh,i}(T)=R_{sh,20,i}\left[1+\alpha_{sh,i}(T-20)\right]
\]

hesaplanır. Varsa GCC/ECC direnci de sıcaklıkla düzeltilir.

Bu dirençler global primitive blokların gerçek ve sanal bileşenleriyle yeniden birleştirilir; böylece core ve kılıf akımları sıcaklık durumuna göre değişebilir.

## 4. Global elektromanyetik çözüm

Fiziksel core ve metalik iletken ağı genel biçimde:

\[
\Delta\mathbf V=\mathbf Z(T)\mathbf I
\]

ile temsil edilir.

Paralel core akımları için yalnız devre/faz toplam kısıtları uygulanır:

\[
\sum_{k=1}^{n_p} I_{p,k}=I_{p,set}
\]

Paralel kablo uçtan uca gerilim düşümleri eşitlenir; kılıf, cross-bonding, link-box, bonding lead, elektrot ve GCC/ECC dalları aynı ağda çözülür.

Aynı sistem iki bağımsız yöntemle çözülür:

- `GLOBAL_DIRECT_KKT`
- `GLOBAL_SHEATH_SCHUR`

Yakınsama kapısı için yöntemlerin akım ve gerilim sonuçlarının tolerans içinde anlaşması zorunludur.

## 5. Kablo bazlı kayıplar

Her fiziksel kablo için:

\[
W_{c,i}=|I_{c,i}|^2R_{ac,i}(T_{c,i})
\]

\[
W_{sh,i}=|I_{sh,i}|^2R_{sh,i}(T_{sh,i})
\]

\[
W_{d,i}=2\pi f C_iU_0^2\tan\delta_i
\]

Geçici zırh gölge kaynağı:

\[
W_{arm,i}=\lambda_{2,i}W_{c,i}
\]

Toplam ısı kaynağı:

\[
W_i=W_{c,i}+W_{sh,i}+W_{d,i}+W_{arm,i}
\]

Kılıf kaybı güzergâh minor section sonuçlarından termal bölgeyle örtüşen uzunluğa göre dağıtılır.

## 6. Gerçek x-y termal çözüm

Her fiziksel kablonun toplam ısı kaynağı gerçek merkez koordinatından ortak 2D sonlu-hacim alanına uygulanır:

\[
-\nabla\cdot(k\nabla T)=q
\]

Aynı anda gerçek x-y analitik karşılıklı termal direnç matrisi de karşılaştırma amacıyla hesaplanır:

\[
\Delta\mathbf T=\mathbf R_{th}\mathbf W
\]

Kapalı çevrim sıcaklık geri beslemesi 2D nodal conductor/jacket sonuçlarını kullanır.

## 7. Kılıf sıcaklığı tahmini

Mevcut veri modelinde metalik kılıf için ayrı tam termal düğüm bulunmadığından kılıf sıcaklığı iletken ve jacket sıcaklıkları arasında şu fiziksel yol üzerinden kestirilir:

\[
T_{sh}=T_c-\left(W_c+0.5W_d\right)T_1
\]

Sonuç:

\[
T_j\le T_{sh}\le T_c
\]

aralığına sınırlandırılır. Bu, ayrı metalik katman termal kapasitesi veya detaylı radyal düğüm çözümünün yerine geçen açık bir ara modeldir.

## 8. Under-relaxation

Yeni termal durum doğrudan kullanılmaz:

\[
T^{(n+1)}_{used}=\beta T^{(n+1)}_{solved}+(1-\beta)T^{(n)}
\]

Burada `beta` varsayılan olarak `0.60` değerindedir ve kullanıcı arayüzünden değiştirilebilir.

## 9. Yakınsama kriterleri

Bir iterasyon ancak aşağıdakilerin tamamı sağlandığında kapanır:

### Sıcaklık residual'ı

\[
\max_i\left|T_i^{solved}-T_i^{state}\right|\le\varepsilon_T
\]

### Core akımı değişimi

\[
100\max_i\frac{|I_{c,i}^{(n)}-I_{c,i}^{(n-1)}|}{\max(|I_{c,i}^{(n-1)}|,1)}\le\varepsilon_I
\]

### Kılıf ve aksesuar akımı değişimi

Aynı göreli kriter kılıf, GCC ve aksesuar dal akımlarına uygulanır.

### Aktif metal kaybı değişimi

\[
100\frac{|P_{active}^{(n)}-P_{active}^{(n-1)}|}{\max(|P_{active}^{(n-1)}|,1)}\le\varepsilon_P
\]

### Sayısal kapılar

- İki bağımsız EM çözümü anlaşmalıdır.
- Bütün termal bölgeler yakınsamış olmalıdır.

## 10. Kapalı çevrim ampacity dış döngüsü

Bütün aktif devrelerin temel akımları aynı faktörle ölçeklenir:

\[
I_{circuit,rating}=k_I I_{circuit,base}
\]

Dış döngü önce sıcaklık sınırını çevreler, ardından bisection uygular:

\[
\max_i T_{c,i}(k_I)=T_{limit}
\]

Dış döngüde her aday faktör için iç elektro-termal kapalı çevrim yeniden çözülür.

Kapanış için:

- sıcaklık sınırına yakınlık,
- akım bracket genişliği,
- iç kapalı çevrim yakınsaması

raporlanır.

Bu yöntem devrelerin göreli yük oranını korur; devre bazında bağımsız optimum rating aramaz.

## 11. Yazılım mimarisi

Yeni ana modül:

`src/ucd/calculations/electrothermal_coupled.py`

Sıcaklık geri beslemesi için eklemeli genişletilen modüller:

- `multiconductor_em.py`
- `multiconductor_global_network.py`
- `multiconductor_thermal.py`

Yeni arayüz:

`src/ucd/ui/electrothermal_coupled_dialog.py`

Mevcut fonksiyonların varsayılan argümanları eski davranışı korur. Yeni sıcaklık girdileri verilmediğinde v0.16.6 üretim/gölge davranışı değişmez.

## 12. Veri bütünlüğü

- Çözüm başında proje `to_dict()` görüntüsü alınır.
- Çözüm sonunda aynı görüntüyle karşılaştırılır.
- Herhangi bir proje mutation görülürse sonuç üretilmeden hata verilir.
- Ampacity dış döngüsü her aday için projenin derin kopyası üzerinde çalışır.
- Proje `lambda1`, kablo katsayıları, termal bölge ve sonuç kayıtlarına write-back yapılmaz.

## 13. Bilinçli sınırlar

- Genel gerçek x-y proximity kaybı henüz tamamlanmamıştır.
- Fiziksel zırh elektromanyetik ve termal modeli henüz tamamlanmamıştır.
- Kılıf sıcaklığı ayrı detaylı radyal metalik düğüm yerine T1 tabanlı ara tahmindir.
- Ampacity ortak devre çarpanı kullanır.
- Motor standart benchmark setleri ve saha karşılaştırmaları tamamlanmadan `PHYSICAL_PRIMARY` yapılmaz.

## 14. Sonraki doğrulama kapısı

v0.16.8 hedefleri:

- IEC/CIGRE doğrulama vakaları,
- legacy–physical shadow karşılaştırması,
- tolerance ve conditioning denetimleri,
- sonuç farklarının neden sınıflandırması,
- yeni motorun üretim motoruna yükseltilmesi için açık kabul kapısı.
