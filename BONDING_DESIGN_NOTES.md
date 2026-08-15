# v0.9 Primitive CIM / Node-Voltage Bonding Notes

## 1. Tek fiziksel ağ

Hesap aşağıdaki branch türlerinden kurulur:

```text
CABLE_SECTION   : 3 sheath + opsiyonel GCC multi-conductor branch
CROSS_LINK      : link-box fazlar arası cross connection
STRAIGHT_LINK   : aynı sheath continuity
SOLID_BOND      : sheath uçları ile ortak bond bus
GCC_LINK/BOND   : ECC/GCC sürekliliği ve grounding bağlantısı
EARTH           : ortak bus ile referans toprak arasındaki elektrot direnci
```

Sheath cross bağlantıları görselden değil `BondingConnection` kayıtlarından gelir.

## 2. Primitive line matrix

Her route contribution için `3 core + 3 sheath (+ GCC)` conductor listesi oluşturulur. Seri empedans:

```text
Zprimitive = Zinternal + Zexternal + Zearth-return
```

v0.9 earth-return modeli:

```text
De = 658.37 sqrt(rho_earth / f)
Re = pi² f 10⁻⁴        ohm/km
Xc = 4 pi f 10⁻⁴       ohm/km

Zii = Ri + Re + jXc ln(De/GMRi)
Zij =      Re + jXc ln(De/Dij)
```

Concentric core–own-sheath mutual distance için mean sheath radius kullanılır.

## 3. Bilinen ve bilinmeyen iletkenler

Core current phasorları bilinir:

```text
IA = I∠0°
IB = I∠-120°
IC = I∠+120°
```

Unknown conductor branch relation:

```text
Vstart - Vend = Zuu · Iunknown + Zuc · Icore
```

Buradaki `Zuc·Icore`, minor section boyunca indüklenen kompleks kaynak vektörüdür.

## 4. Shunt admittance

Her phase core–sheath için:

```text
Y = omega C tan(delta) + j omega C
```

section uçlarına yarım yarım dağıtılır. Core phase voltage bilinen kaynak kabul edilerek sheath node denklemine eklenir.

## 5. CIM / MNA

```text
G·V + A·I = J
Aᵀ·V - Z·I = E
```

Augmented kompleks sistem tek seferde çözülür.

## 6. Node Voltage

Branch akımları elimine edilir:

```text
I = Z⁻¹(AᵀV - E)
(G + AZ⁻¹Aᵀ)V = J + AZ⁻¹E
```

CIM ve NV aynı ağdan geldiği için farkları yazılım hatası veya kötü koşulluluk göstergesidir.

## 7. Kayıplar

Ayrı raporlanır:

- metalik kılıf `I²R`,
- GCC/ECC metal `I²R`,
- primitive branch real-power içindeki eşdeğer earth-return kısmı,
- link, bond ve ground-electrode kayıpları.

IEC 60287'ye yalnız metalik kılıf longitudinal loss oranı `lambda1` olarak gönderilir.

## 8. Cross-bonding iterasyonu

Mevcut otomatik yerleşim, önce standing-voltage ve open-circuit residual EMF ile joint sınırlarını üretir. Son tasarım primitive ağla doğrulanır.

Sonraki optimizer amaç fonksiyonu doğrudan şunları kullanacaktır:

```text
max sheath current
max sheath-to-ground voltage
total metalik kılıf loss
lambda1
GCC current/loss
joint/link-box count and cost
CAD candidate feasibility
```

## 9. Model sınırları

- simplified-Carson ortak toprak dönüşü,
- dengeli üç faz core akımı,
- tek devre Trefoil/Flat geometri,
- power-frequency çözüm,
- SVL open-circuit normal-state varsayımı.

Fault/EPR, frequency dependence, nonlinear SVL ve full earth integral sonraki sürümlerdir.
