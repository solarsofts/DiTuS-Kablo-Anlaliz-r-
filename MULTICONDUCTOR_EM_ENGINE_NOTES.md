# v0.16.5 Genel N‑İletken Elektromanyetik Motor — Teknik Notlar

## 1. Amaç ve mimari sınır

v0.16.5, `InstallationCrossSectionData` içindeki gerçek fiziksel kablo nesnelerini ilk kez elektromanyetik bir çözüme bağlar. Motor mevcut bonding/CIM ve IEC sonuç yolunun üstüne yazmaz; `SHADOW_COMPARE` çalışır.

Girdi:

- fiziksel kesit,
- aktif devreler,
- devre/faz toplam kompleks akımları,
- her fiziksel kablonun x ve derinlik koordinatı,
- core ve metalik kılıf elektriksel parametreleri,
- toprak elektriksel özdirenci,
- isteğe bağlı GCC/ECC.

Çıktı:

- her fiziksel core akımı,
- her fiziksel kılıf akımı,
- GCC/ECC akımı,
- devre/faz ortak boyuna gerilim düşümü,
- core ve kılıf metal kayıpları,
- açık-devre kılıf EMF’si,
- shadow λ1,
- residual, condition number ve iki çözüm yöntemi farkı.

## 2. Primitive iletken sırası

Aktif fiziksel kablo sayısı `N` ise:

```text
C:<physical-cable-1>
...
C:<physical-cable-N>
S:<physical-cable-1>
...
S:<physical-cable-N>
[GCC]
```

oluşturulur.

GCC kapalıysa primitive matris boyutu `2N × 2N`; açıksa `(2N+1) × (2N+1)` olur.

## 3. Primitive empedans

Mevcut doğrulanmış power-frequency kernel korunur:

\[
Z_{ii}=R_i+R_e+jX_c\ln\left(\frac{D_e}{GMR_i}\right)
\]

\[
Z_{ij}=R_e+jX_c\ln\left(\frac{D_e}{D_{ij}}\right)
\]

\[
D_e=658.37\sqrt{\frac{\rho_e}{f}},\qquad
R_e=\pi^2f10^{-4},\qquad
X_c=4\pi f10^{-4}
\]

Matris fiziksel x-y mesafelerinden kurulur ve kompleks simetriktir.

Bu, simplified-Carson eşdeğer derinlik yaklaşımıdır. Tam Carson integral, Pollaczek, Wedepohl–Wilcox, Ametani ve wideband EMT modeli değildir.

## 4. Core ve metalik iletken partition

Primitive denklem:

\[
\begin{bmatrix}
\Delta\mathbf V_c\\
\Delta\mathbf V_m
\end{bmatrix}
=
\begin{bmatrix}
\mathbf Z_{cc} & \mathbf Z_{cm}\\
\mathbf Z_{mc} & \mathbf Z_{mm}
\end{bmatrix}
\begin{bmatrix}
\mathbf I_c\\
\mathbf I_m
\end{bmatrix}
\]

Burada metalik bilinmeyenler `N` adet kılıf ve varsa GCC/ECC’dir.

## 5. Faz toplamı kısıtları

Her devre–faz grubu için paralel core akımlarının toplamı proje sınır koşuluna eşittir:

\[
\mathbf B^T\mathbf I_c=\mathbf I_{set}
\]

`B`, fiziksel core ile devre/faz grubu arasındaki incidence matrisidir.

Aynı devre–faz grubundaki paralel kabloların boyuna gerilim düşümü aynıdır:

\[
\Delta\mathbf V_c=\mathbf B\mathbf V_g
\]

Bu nedenle akımlar eşit kabul edilmez; empedans ve mutual coupling tarafından çözülür.

## 6. Doğrudan KKT çözümü

Yerel iki uçtan bağlı metalik iletkenlerde:

\[
\Delta\mathbf V_m=0
\]

ve sistem:

\[
\begin{bmatrix}
\mathbf Z_{cc} & \mathbf Z_{cm} & -\mathbf B\\
\mathbf Z_{mc} & \mathbf Z_{mm} & \mathbf 0\\
\mathbf B^T & \mathbf 0 & \mathbf 0
\end{bmatrix}
\begin{bmatrix}
\mathbf I_c\\
\mathbf I_m\\
\mathbf V_g
\end{bmatrix}
=
\begin{bmatrix}
\mathbf 0\\
\mathbf 0\\
\mathbf I_{set}
\end{bmatrix}
\]

olarak çözülür.

Açık kılıf sınırında:

\[
\mathbf I_m=0
\]

ve yalnız core KKT sistemi çözülür.

## 7. Schur-complement doğrulaması

İki uçtan bağlı durumda metalik akımlar:

\[
\mathbf I_m=-\mathbf Z_{mm}^{-1}\mathbf Z_{mc}\mathbf I_c
\]

olur. Core eşdeğer empedansı:

\[
\mathbf Z_{eff}=\mathbf Z_{cc}-
\mathbf Z_{cm}\mathbf Z_{mm}^{-1}\mathbf Z_{mc}
\]

ve grup admitans matrisi:

\[
\mathbf Y_g=\mathbf B^T\mathbf Z_{eff}^{-1}\mathbf B
\]

ile:

\[
\mathbf V_g=\mathbf Y_g^{-1}\mathbf I_{set}
\]

\[
\mathbf I_c=\mathbf Z_{eff}^{-1}\mathbf B\mathbf V_g
\]

hesaplanır.

Doğrudan KKT ve Schur sonuçlarının farkı kabul kapısıdır.

## 8. Açık-devre kılıf EMF’si

Açık kılıf için metalik iletkenlerdeki indüklenen boyuna EMF:

\[
\mathbf E_{open}=\mathbf Z_{mc}\mathbf I_c
\]

olarak raporlanır.

Yerel iki uçtan bağlı durumda çözülen metalik akımın empedans düşümü bu EMF’yi dengeler:

\[
\mathbf Z_{mc}\mathbf I_c+
\mathbf Z_{mm}\mathbf I_m\approx0
\]

## 9. Kayıplar

Her core:

\[
P_{c,i}=|I_{c,i}|^2R_{ac,i}\quad[W/km]
\]

Her metalik kılıf:

\[
P_{sh,i}=|I_{sh,i}|^2R_{sh,i}\quad[W/km]
\]

Shadow kılıf kayıp faktörü:

\[
\lambda_1^{shadow}=
\frac{\sum_iP_{sh,i}}{\sum_iP_{c,i}}
\]

GCC/ECC kaybı λ1’e dahil edilmez ve ayrı raporlanır.

## 10. Rac kaynağı

Core direnci için öncelik:

1. v0.16.4 fiziksel Rac shadow sonucu,
2. desteklenmeyen iletken yapısında kilitli legacy Rac fallback.

Önemli sınırlama: v0.16.4 proximity faktörü tek güzergâh faz aralığına dayanır. v0.16.5 arbitrary x-y mutual empedansı kullanır ancak proximity iç kaybını henüz genel N-kablo geometrisinden yeniden hesaplamaz.

## 11. Kapsam dışı

- genel N-core/N-sheath explicit cross-bonding link-box ağı,
- farklı kablo tiplerinin aynı kesitte registry ile çözümü,
- fiziksel akım override’lı karışık kısıt sistemi,
- zırh primitive modeli,
- sequence impedance ve fault-current çözümü,
- tam earth-return integralleri,
- frequency-dependent EMT,
- yeni shadow λ1’in otomatik IEC/termal aktarımı.

## 12. Sonraki v0.16.5 kapısı

1. N-kablo section primitive bloklarının mevcut minor-section ağına adaptasyonu,
2. her fiziksel kılıf için link-box terminal düğümleri,
3. çok devreli cross-bonding bağlantı grafiği,
4. kılıf-toprak ve kılıf-kılıf düğüm gerilimleri,
5. kablo bazlı λ1 ve kayıp defterinin termal motora kontrollü aktarımı,
6. IEEE/IEC doğrulama vaka setleri ve formasyon karşılaştırması.
