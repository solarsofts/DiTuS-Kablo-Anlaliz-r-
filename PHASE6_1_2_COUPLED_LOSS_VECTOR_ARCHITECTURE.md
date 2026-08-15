# FAZ 6.1–6.2 — Senaryo Bazlı Kayıp Vektörü ve Üretim Elektro-Termal Çevrimi

## Amaç

Bu faz, IEEE 575 bonding ağı ile gerçek x-y termal model arasındaki kayıp geri beslemesini UI dışındaki saf hesap katmanında kapatır. Üretim hesabı artık tek bir global `λ1`, tek skaler akım veya eşit kayıplı T4 satır toplamı kullanmaz.

## Tek çalışma noktası

Her NORMAL, DESIGN ve devre-bazlı N-1 senaryosu aşağıdaki verileri taşır:

- devre bazında fiziksel varlık, enerjilenme ve RMS faz akımı,
- fiziksel kablo bazında fazör akım ve açık override kaynağı,
- hedef devre ve ampacity ölçekleme modu,
- senaryo, geometri ve kayıp vektörü fingerprint'leri.

Fiziksel kablo devre dışı kaldığında kesit geometrisinden silinmez. İletken, kılıf ve dielektrik kayıpları sıfırlanır. Enerjili fakat sıfır yüklü kabloda dielektrik kayıp korunur; `λ1` uygulanabilir değildir.

## Üretim çevrimi

`solve_production_electrothermal_study()` şu kapalı çevrimi çalıştırır:

1. Senaryo ve fiziksel akım vektörünü çözer.
2. Sıcaklığa bağlı iletken ve metalik kılıf dirençlerini kurar.
3. Global N-core/N-sheath/link-box/GCC ağını çözer.
4. Fiziksel kablo kayıp vektörünü üretir.
5. Gerçek x-y termal direnç matrisi ile `Rth × q` sıcaklık artışını çözer.
6. İletken ve kılıf sıcaklıklarını geri besler.
7. Sıcaklık, akım ve aktif kayıp residual'ları yakınsayana kadar iterasyon yapar.

Proje nesnesi ve `cable.sheath_loss_factor` değiştirilmez.

## λ1 sözleşmesi

`λ1`, üretim girdisi değildir:

`λ1_i = Psheath_i / Pconductor_i`

İletken kaybı sıfırsa değer `NOT_APPLICABLE`/`None` olur. Global `cable.sheath_loss_factor` yalnız fiziksel bonding ağı bulunmayan legacy çözümler için fallback olarak kalır.

## T4 ve kayıp vektörü

Termal üretim otoritesi:

`Δθ_external = Rth_matrix × q_vector`

Burada `q_vector`, her fiziksel kablonun iletken, kılıf, zırh ve dielektrik kayıplarını taşır. T4 satır toplamı yalnız eşit-kayıp diagnostic'idir; farklı yüklü veya devre dışı devrelerde üretim sonucu değildir.

## N-1

N-1, tek skaler senaryo değildir. Her devre için ayrı devre-dışı çalışma noktası üretilir. Devre konumları asimetrikse C1-out ve C2-out sonuçları ayrı kalır. Yalnız tam akım ve enerjilenme vektörleri aynıysa alias yapılabilir.

## Ampacity

- `COMMON_SCALE`: seçili aktif akım vektörünün tamamını birlikte ölçekler.
- `TARGET_CIRCUIT_SCALE`: hedef devreyi ölçekler, arka plan devrelerini sabit tutar.

Sonuç hedef devreleri, sabit arka plan akımlarını ve ölçek modunu açıkça taşır.

## Analitik–nodal doğrulama

`validate_production_thermal_methods()` analitik üretim çalışma noktasındaki dondurulmuş global akım/kayıp vektörünü hem analitik hem nodal termal motora verir. İki yöntemin `loss_vector_fingerprint` değeri aynı olmak zorundadır. Nodal yakınsama, enerji dengesi ve residual kapıları ayrıca raporlanır.

## Kapsam sınırı

- `load_factor`, kararlı durum RMS akımını küçültmez; çevrimsel yük semantiği FAZ 6.5'e bırakılmıştır.
- Skin/proximity katsayı formülleri FAZ 6.3'e bırakılmıştır.
- Toprak kuruması FAZ 6.4'e bırakılmıştır.
- Paralel devrelerin ayrıntılı standing-voltage ve çok-devre kılıf indüksiyonu FAZ 6.6–6.7'de derinleştirilecektir.
