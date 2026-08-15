# Sheath Loss Completeness Closure — v0.16.9.4.34

## Bağlayıcı karar

Global primitive ağın kılıf sonucu yalnız çözülen boyuna metalik kılıf dal akımlarının `Σ|I|²R` kaybıdır. Bu oran `network_sheath_loss_ratio` olarak izlenir; IEC 60287 kapalı-form `λ1′` ile cebirsel özdeşlik iddiası yoktur.

IEC rating için kullanılan kılıf kayıp oranı iki provenance bileşeninden oluşur:

`lambda1_rating = network_sheath_loss_ratio + lambda1_eddy`

`lambda1_eddy`, yalnız uygulanabilir IEC 60287-1-1 kapsamı veya aktif proje koşullarıyla doğrulanmış harici kayıt üzerinden kullanılabilir.

## IEC karar kapısı

- Explicit wire screen + equalizing strip / thin sheet kanıtı: `IEC_2.3.6.1_NOTE_3_NEGLIGIBLE`, `lambda1_eddy=0`, FULL.
- Solid both-end + non-Milliken: IEC 2.3 giriş kapsamı uyarınca ek eddy terimi aranmaz, FULL.
- Büyük dilimli Milliken: 2.3.6.1 eddy terimi 2.3.5 `F` faktörüyle birlikte uygulanır.
- Cross-bonded / single-point + tekli devre + desteklenen Trefoil/Flat: 2.3.6.1 kapalı form otomatik hesaplanır, FULL.
- `m <= 0.1`: yalnız `Δ1` ve `Δ2` düşürülür; `λ0` korunur.
- CUSTOM veya paralel/çok-devre: tek-devre kapalı form otomatik uygulanmaz. Aktif koşullarla uyumlu izlenebilir harici `λ1″` yoksa IEC ampacity üretim otoritesi BLOCKED.
- Büyük/kalın Al kılıf: Note 2 evidence kodu üretilir.

## Harici λ1″ sözleşmesi

Harici kayıt değer, kaynak türü/referansı, frekans, kılıf sıcaklığı, `d`, `s` ve formasyon varsayımını taşır. Referans koşulları aktif projeyle uyuşmazsa `STALE_EXTERNAL_LAMBDA1_EDDY_*` nedeni ile kullanılmaz.

## Sonuç yüzeyi

Üretim çalışma noktası ve rapor ayrı ayrı `λ1′ network`, `λ1″ eddy`, `λ1 rating`, authority, kaynak ve reason-code gösterir. Bonding ekranındaki network oranı artık toplam IEC `λ1` olarak etiketlenmez.

Ampacity dış döngüsü sheath-loss completeness FULL değilse fail-closed durur. Çalışma noktası/shadow sonucu hesaplanabilir ve eksik fizik açık authority/reason-code ile görülebilir.

## DiTuS geometri politikası

IEC kapalı formları arbitrary x-y geometri için genişletilmez. Trefoil/Flat sınıflandırması önce yapısal geometriyi kontrol eder, sonra ideal formasyon varsayımının `λ1″` sonuç duyarlılığını DiTuS mühendislik bütçesi içinde doğrular. Bu tolerans IEC normatif toleransı olarak sunulmaz.
