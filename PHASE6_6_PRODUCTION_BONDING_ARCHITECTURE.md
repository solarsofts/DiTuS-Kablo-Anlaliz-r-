# FAZ 6.6 — Üretim Bonding Otoritesi

## Karar

Bonding/CIM ekranının üretim otoritesi artık ayrı tek-devre üç-loop hesabı değildir. NORMAL, DESIGN ve her devre-bazlı N-1 çalışma noktası, FAZ 6.1–6.2'de üretim zincirine alınan aynı global N-core/N-kılıf/link-box/GCC ağından özetlenir.

## Fiziksel kapsam

- Her fiziksel core/kılıf `Devre + Faz + Paralel No` kimliğiyle aynı ağda bulunur.
- Paralel devrelerin karşılıklı manyetik katkısı primitive matris içinde doğrudan çözülür; dış devre katkısı ayrı bir yaklaşık terim olarak eklenmez.
- Devre akımları `ResolvedOperatingScenario` üzerinden gelir. N-1 için devre-dışı devre geometriden silinmez; core/kılıf aktif kaybı ve terminal akımı sıfırlanır.
- Kılıf direnci, kapalı çevrim elektro-termal çözümde bulunan gerçek kılıf sıcaklığından beslenir.
- Global ağın direct ve reduced çözümleri aynı fizik ağından bağımsız doğrulama kapısıdır.

## Legacy üç-loop rolü

`solve_project_bonding()` ve mevcut üç-loop tabloları çizim, minör/major section tanısı ve geriye dönük karşılaştırma için korunur. Üretim otoritesi değildir. UI ve rapor bu ayrımı açıkça gösterir.

## Sıcaklık düzeltmesi

20 °C altındaki metalik kılıf sıcaklığı artık yapay olarak 20 °C'ye kırpılmaz veya reddedilmez. `R(T)=R20[1+alpha20(T-20)]` fiziksel sıcaklıkta uygulanır. Mutlak sıfır sınırı korunur; düzeltme sıfır veya negatif direnç üretirse çözüm fail-closed durur. Aynı ilke GCC/ECC direncine de uygulanır.

## FAZ 6.7 sınırı

Bu faz kümülatif açık-devre standing-voltage profilini değiştirmez. Global ağın düğüm `Vsheath-earth` ve `Vsheath-sheath` sonuçları üretim çalışma noktasıdır; minör açık-devre fazör profilinin güzergâh boyunca kümülatif yeniden kurulması FAZ 6.7'dir.
