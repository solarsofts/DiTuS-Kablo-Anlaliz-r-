# v0.16.4 — Kablo Fiziksel Parametre Motoru Teknik Notları

## 1. Mimari konum

Yeni motor mevcut hesap çekirdeğinin yerine geçmez:

```text
ProjectData.cable + seçili RouteSection
                 │
                 ▼
Physical Cable Parameter Engine
                 │
                 ├── fiziksel sonuç
                 ├── legacy karşılaştırma
                 ├── sorunlar / veri kapıları
                 └── hesap izi

Mevcut IEC 60287 / bonding / termal solver girdileri değişmez.
```

Çalışma modu:

```text
SHADOW_COMPARE
```

Amaç, fiziksel motor doğrulanmadan önce mevcut sonucu değiştirmemek ve her farkın nedenini görünür kılmaktır.

## 2. Veri önceliği

### İletken Rdc20

1. Üretici/test/proje `Rdc20` girdisi
2. Yoksa malzeme özdirenci ve gerçek metal kesitinden ön hesap

Geometrik kontrol:

\[
R_{dc,20}=\frac{\rho_{20}\,10^9}{A_{metal}}\quad[\Omega/km]
\]

Sıcaklık düzeltmesi:

\[
R_{dc}(\theta)=R_{dc,20}\left[1+\alpha_{20}(\theta-20)\right]
\]

Geometrik sonuç, sertifikalı değer varsa onu geçersiz kılmaz; yalnız farkı raporlar.

## 3. IEC tabanlı AC direnç katmanı

Boyutsuz parametreler:

\[
x_s^2=\frac{8\pi f}{R_{dc}(\theta)_{\Omega/m}}10^{-7}k_s
\]

\[
x_p^2=\frac{8\pi f}{R_{dc}(\theta)_{\Omega/m}}10^{-7}k_p
\]

Skin faktörü:

\[
y_s=\frac{x_s^4}{192+0.8x_s^4}\qquad x_s\leq2.8
\]

\[
y_s=-0.136-0.0177x_s+0.0563x_s^2\qquad 2.8<x_s\leq3.8
\]

\[
y_s=0.354x_s-0.733\qquad x_s>3.8
\]

Üç tek damarlı kablo için proximity faktörü:

\[
y_p=\frac{x_p^4}{192+0.8x_p^4}
\left(\frac{d_c}{s}\right)^2
\left[
0.312\left(\frac{d_c}{s}\right)^2+
\frac{1.18}{\frac{x_p^4}{192+0.8x_p^4}+0.27}
\right]
\]

AC direnç:

\[
R_{ac}(\theta)=R_{dc}(\theta)(1+y_s+y_p)
\]

Bu sürümde `s`, seçili legacy güzergâh bölümünün faz eksen aralığıdır. Serbest x-y çoklu kablo geometrisi sonraki N-iletken elektromanyetik katmanda çözülecektir.

## 4. ks/kp veri kapısı

Motor yalnız açıkça desteklenen yuvarlak iletken yapılarını otomatik sınıflandırır. Özellikle Cu Milliken için farklı tel yapıları farklı katsayı çiftlerine sahip olduğundan tel profili bilinmeden değer uydurulmaz.

Desteklenmeyen bir yapı için iki seçenek vardır:

- üretici/standart kaynağı belirtilmiş açık `ks` ve `kp` çifti,
- fiziksel hesap blokajı.

Tek katsayı girilip diğeri boş bırakılırsa çift tamamlanmış kabul edilmez.

## 5. Kapasitans ve dielektrik kayıp

Ana izolasyon katmanı için koaksiyel kontrol:

\[
C'=\frac{2\pi\varepsilon_0\varepsilon_r}
{\ln(D_{out}/D_{in})}\quad[F/m]
\]

Faz-toprak gerilimi:

\[
U_0=\frac{U_{LL}}{\sqrt3}
\]

Dielektrik kayıp:

\[
W_d=2\pi f C'U_0^2\tan\delta\quad[W/m]
\]

Üretici/test kapasitansı varsa ana girdi olmaya devam eder; geometrik değer tutarlılık kontrolüdür.

## 6. Metalik kılıf direnci

Metalik kılıf gerçek metal kesiti biliniyorsa:

\[
R_{sh,20}=\frac{\rho_{sh,20}\,10^9}{A_{sh}}\quad[\Omega/km]
\]

Bu sonuç, mevcut bonding motorundaki kılıf akımı çözümünün yerine geçmez. Sonraki entegrasyonda kılıf direnci fiziksel parametre resolver üzerinden primitive ağın girdisi olacaktır.

## 7. GMR ve termal katmanlar

Eşdeğer iletken yarıçapı:

\[
r_{eq}=\sqrt{A/\pi}
\]

Üretici GMR değeri yoksa yalnız dolu yuvarlak eşdeğer yaklaşımı gösterilir:

\[
GMR\approx0.7788r_{eq}
\]

Çok telli iletkende bu değer nihai kabul edilmez ve uyarı üretir.

T1–T3, kilitli mevcut fiziksel katman çözümünden okunur; v0.16.4 bu denklemleri ikinci kez kopyalamaz.

## 8. Sonuç statüsü

`final_design_ready`, yalnız v0.16.4 fiziksel parametre hesabının desteklenen veriyle hata vermeden tamamlanmasını ifade eder. Projenin IEC/bonding/termal nihai mühendislik onayı değildir.

Aşağıdaki durumlar sonucu koşullu/bloke yapabilir:

- desteklenmeyen iletken yapısı,
- eksik Cu Milliken tel profili,
- geçersiz faz aralığı,
- eksik izolasyon katmanı,
- çözülmemiş zırh fiziği.

## 9. Sonraki bağlantı

v0.16.5 genel N-iletken motorunda:

- her fiziksel core,
- her sheath/screen,
- varsa armour,
- GCC/ECC ve bonding dalları

ortak x-y geometri ve kompleks ağda çözülecektir. v0.16.4 sonuçları o motorun kablo-içi parametre sağlayıcısı olacaktır.

## FAZ 6.3 üretim geçişi

v0.16.9.4.24 itibarıyla ks/kp -> ys/yp -> Rac(T) yolu bilinen iletken konstrüksiyonlarında shadow karşılaştırma olmaktan çıkmış ve üretim IEC/EM/termal zincirine bağlanmıştır. Eski ys/yp skalerleri yalnız açık legacy fallback'tir. Tam arbitrary-x/y proximity genellemesi bu fazın kapsamı dışındadır.
