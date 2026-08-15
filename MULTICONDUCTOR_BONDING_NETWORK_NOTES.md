# v0.16.5.1 Genel N‑İletken Bonding Ağı — Teknik Notlar

## 1. Mimari konum

Motor, v0.16.5 yerel N‑iletken kesit çözümünün üzerine eklenen ayrı bir gölge ağ katmanıdır:

```text
InstallationCrossSectionData
        ↓
Yerel N-core akım paylaşımı
        ↓
Minor-section primitive blokları
        ↓
Fiziksel N-sheath + GCC ağ grafiği
        ↓
CIM/MNA  ↔  Node-Voltage
```

Mevcut tek-devre `primitive_cim` motoru üretim motoru olarak kilitli kalır.

## 2. Fiziksel kılıf kimliği

Ağda her kılıf şu anahtarla tanımlanır:

```text
Circuit ID + Phase + Parallel Index
```

Örnek:

```text
C1:A:P1
C1:A:P2
C2:C:P1
```

Fiziksel kablo ID’si kesitten okunur; ağ sürekliliği anahtar üzerinden kurulur. Güzergâh boyunca anahtar seti değişirse çözüm durur. Sessiz kablo eşleme yapılmaz.

## 3. Minor-section blok integrasyonu

Her minor section, güzergâh ve termal bölge sınırlarında alt parçalara ayrılır. Her alt parçada bağlı fiziksel kesit seçilir.

Yerel primitive matris:

\[
\begin{bmatrix}
\Delta\mathbf V_c\\
\Delta\mathbf V_s
\end{bmatrix}
=
\begin{bmatrix}
\mathbf Z_{cc}&\mathbf Z_{cs}\\
\mathbf Z_{sc}&\mathbf Z_{ss}
\end{bmatrix}
\begin{bmatrix}
\mathbf I_c\\
\mathbf I_s
\end{bmatrix}
\]

Yerel core akımı, v0.16.5 N‑iletken akım paylaşımıyla bulunur. Kılıf ağına uygulanan dağıtılmış kaynak:

\[
\mathbf E_s=\mathbf Z_{sc}\mathbf I_c
\]

Minor section boyunca:

\[
\mathbf Z_{ss,minor}=\sum_r \mathbf Z_{ss,r}\,L_r
\]

\[
\mathbf E_{minor}=\sum_r \mathbf Z_{sc,r}\mathbf I_{c,r}\,L_r
\]

Buradaki uzunluk ölçeği kilometredir.

## 4. Link-box bağlantısı

Mevcut bonding bağlantısı:

```text
A-L → B-R
B-L → C-R
C-L → A-R
```

her devre ve paralel indeks için ayrı uygulanır:

```text
C1:A:P1 → C1:B:P1
C1:A:P2 → C1:B:P2
C2:A:P1 → C2:B:P1
```

Devre ve paralel kimliği korunur.

Bu, mevcut faz permütasyon veri modelinden türetilen bağlantıdır. Kullanıcının her fiziksel terminali tek tek eşlediği explicit terminal matrix henüz eklenmemiştir.

## 5. Kompleks ağ denklemi

Tüm cable-section ve aksesuar dalları için incidence matrisi `A`, dal empedans matrisi `Z`, şönt admitans `G`, kaynak vektörleri `E/J` oluşturulur.

CIM/MNA:

\[
\begin{bmatrix}
\mathbf G&\mathbf A\\
\mathbf A^T&-\mathbf Z
\end{bmatrix}
\begin{bmatrix}
\mathbf V\\
\mathbf I
\end{bmatrix}
=
\begin{bmatrix}
\mathbf J\\
\mathbf E
\end{bmatrix}
\]

Node-Voltage:

\[
(\mathbf G+\mathbf A\mathbf Z^{-1}\mathbf A^T)\mathbf V
=\mathbf J+\mathbf A\mathbf Z^{-1}\mathbf E
\]

\[
\mathbf I=\mathbf Z^{-1}(\mathbf A^T\mathbf V-\mathbf E)
\]

İki yöntem aynı ağdan bağımsız çözüm üretir.

## 6. Dielektrik charging

Etkinse her fiziksel kablo için core-kılıf pi şöntü uygulanır:

\[
Y'=\omega C\tan\delta+j\omega C
\]

Her section ucuna `Y'L/2` bağlanır ve bağlı faz gerilimiyle Norton enjeksiyonu oluşturulur.

## 7. Sonuçlar

Her fiziksel kılıf için:

- `Ish` kompleks akımı,
- section başlangıç ve bitiş `Vsheath-earth`,
- entegre açık-devre EMF,
- metal kaybı.

Section için:

\[
P_{sh}=\sum_i |I_{sh,i}|^2R_{sh,i}
\]

Kılıf-kılıf gerilimi:

\[
V_{ij}=V_{sh,i}-V_{sh,j}
\]

Güzergâh gölge kayıp oranı:

\[
\lambda_1^{shadow}=\frac{\sum P_{sh}}{\sum P_c}
\]

Bu değer projeye yazılmaz.

## 8. Legacy eşdeğerlik kapısı

Tek devre, tek paralel ve legacy-projection geometri için yeni ağ:

- maksimum kılıf akımı,
- maksimum kılıf-toprak gerilimi,
- toplam kılıf metal kaybı,
- minor section sonuçları

bakımından kilitli `primitive_cim` sonucu ile eşleşir.

## 9. Kalan fiziksel boşluk

Mevcut çözümde core akımları section-local hesaplanır. Tam fiziksel global çözümde core dalları da ağ bilinmeyeni olmalı ve şu kısıtlar aynı sistemde bulunmalıdır:

\[
\sum_{k=1}^{n_p} I_{c,p,k}=I_{p,set}
\]

Ayrıca her fiziksel core’un joint sürekliliği ve terminal phase bus bağlantısı açık grafikte kurulmalıdır. Bu, sonraki N‑iletken kapısının ana konusudur.
