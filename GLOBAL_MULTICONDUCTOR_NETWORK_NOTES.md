# v0.16.5.2 Global N‑Core + N‑Kılıf Ağ Teknik Notları

## 1. Önceki kapıdan farkı

v0.16.5.1’de her fiziksel kesit için paralel core paylaşımı `OPEN_SHEATH` sınır koşuluyla yerel çözülüyor, bu yerel akımlar kılıf ağına indüklenen kaynak olarak aktarılıyordu.

v0.16.5.2’de her fiziksel core için yalnız bir güzergâh akımı vardır. Aynı `Ic` vektörü bütün route/minor-section primitive bloklarında kullanılır. Core paylaşımı, gerçek kılıf/link-box/toprak/GCC ağına bağlı olarak çözülür.

## 2. Fiziksel kimlik

Süreklilik anahtarı:

```text
Devre + Faz + Paralel No
```

Örnek:

```text
C1:A:P1
C1:A:P2
C2:C:P1
```

Güzergâh boyunca bu anahtarların eklenmesi/çıkarılması sessizce eşlenmez; joint/branch modeli oluşana kadar çözüm bloke edilir.

## 3. Blok denklemleri

Her fiziksel güzergâh bloğu için:

\[
\begin{bmatrix}
\Delta V_c\\
\Delta V_u
\end{bmatrix}
=
\begin{bmatrix}
Z_{cc}&Z_{cu}\\
Z_{uc}&Z_{uu}
\end{bmatrix}
\begin{bmatrix}
I_c\\I_u
\end{bmatrix}
\]

`u` vektörü fiziksel kılıfları ve varsa GCC/ECC’yi içerir.

Güzergâh core gerilim denklemi:

\[
Z_{cc,\Sigma}I_c+H I_u-BV_g=0
\]

Faz toplam kısıtı:

\[
B^T I_c=I_{set}
\]

Kılıf ağı:

\[
GV_s+A I_u=J
\]

\[
A^T V_s-Z_u I_u=C I_c
\]

## 4. Schur doğrulaması

Kılıf ağı:

\[
M_s
\begin{bmatrix}V_s\\I_u\end{bmatrix}
=
\begin{bmatrix}J\\C I_c\end{bmatrix}
\]

olduğundan:

\[
I_u=I_{u0}+K_I I_c
\]

ve indirgenmiş core sistemi:

\[
\left(Z_{cc,\Sigma}+H K_I\right)I_c-BV_g=-H I_{u0}
\]

\[
B^T I_c=I_{set}
\]

şeklinde çözülür. Direct ve reduced sonuçlar bağımsız anlaşma kapısıdır.

## 5. Kayıplar

Her core:

\[
P_{c,i}=|I_{c,i}|^2\sum_b R_{c,i,b}L_b
\]

Her kılıf section dalı:

\[
P_{sh,i,s}=|I_{sh,i,s}|^2R_{sh,i,s}
\]

Gölge kayıp oranı:

\[
\lambda_1^{shadow}=\frac{\sum P_{sh}}{\sum P_c}
\]

Aksesuar, GCC ve eşdeğer earth-return kayıpları ayrı tutulur.

## 6. Sonuç kapıları

- Direct ↔ reduced core akım farkı.
- Direct ↔ reduced sheath/aksesuar dal akımı farkı.
- Düğüm gerilim farkı.
- Faz toplam akım residual’ı.
- Sheath KCL residual’ı.
- Sheath dal gerilim residual’ı.
- Core güzergâh gerilim residual’ı.
- Proje mutation kontrolü.

## 7. Henüz üretim sonucu değildir

`SHADOW_COMPARE` korunur. Bu sonuç:

- proje `λ1` alanına yazılmaz,
- IEC ampacity’yi değiştirmez,
- 2D termal ısı kaynaklarını değiştirmez,
- raporun nihai tasarım sonucuna otomatik aktarılmaz.

Bir sonraki ana kapı, bu global kayıpları gerçek fiziksel kesitli çoklu-kablo termal motora gölge kaynak olarak bağlamaktır.
