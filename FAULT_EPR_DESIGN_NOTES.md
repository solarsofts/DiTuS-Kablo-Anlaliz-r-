# v0.9.0 — Power-Frequency Fault, EPR and SVL-TOV

## Amaç

v0.9.0, v0.8 primitive iletken/metalik-kılıf/GCC/grounding ağını normal yük dışında güç frekanslı arıza akım setleriyle çözer. Aynı fiziksel ağ iki bağımsız yöntemle çalıştırılır:

- `PRIMITIVE_CIM`: augmented complex impedance matrix / MNA
- `NODE_VOLTAGE`: branch-admittance eliminasyonu

CIM ve Node-Voltage farkı, denklem residual'ı ve KCL residual'ı kabul kapısıdır.

## Desteklenen senaryolar

- Üç faz simetrik arıza
- Faz-faz arızası
- Tek faz-toprak arızası

Faz akımları kullanıcı tarafından rms phasor büyüklüğü ve faz seçimiyle tanımlanır. Arıza temizleme süresi ayrı girdidir.

## Hesaplanan görevler

- Minor-section bazında sheath akımları
- GCC/ECC akımı
- Sheath metal kaybı
- Eşdeğer earth-return kaybı
- Toprak elektrodu akımları
- Ground-bus EPR
- Maksimum sheath–yerel toprak gerilimi
- Sectionalizing-joint iki yarısı arasındaki maksimum güç-frekansı gerilimi
- SVL seçimine aktarılabilen yönetici TOV gerilim/süre görevi

## Model sınırları

Bu sürüm güç-frekansı ağ çalışmasıdır. Şunlar henüz yoktur:

- Tam Pollaczek integral çözümü
- Wedepohl–Wilcox veya Ametani wideband parametreleri
- Dağıtılmış grounding-grid yüzey potansiyeli
- Dokunma ve adım gerilimi kontur çözümü
- Ark, fault-location ve kaynak empedansı ağı
- Frekans bağımlı EMT
- Doğrusal olmayan MOV/SVL zaman alanı ve enerji integrali

Toprak elektrotları remote-earth'e bağlı lumped dirençlerdir. Bu nedenle EPR, elektrot düğüm gerilimidir; saha yüzeyi dokunma/adım gerilimi değildir.

## SVL aktarımı

Yönetici power-frequency TOV:

- maksimum sheath–yerel toprak rms gerilimi ile
- maksimum sectionalizing-interrupt rms geriliminin

büyüğü olarak alınır. Süre, senaryo temizleme süresine proje tarafından belirlenen çarpanın uygulanmasıyla SVL TOV kontrolüne aktarılır. Varsayılan çarpan `2.0` olup kullanıcı tarafından değiştirilebilir; evrensel bir kabul değeri olarak kilitlenmemiştir.
