# Baseline Lock — v0.16.9.4.26

Bu sürüm FAZ 6.5 kararlı durum RMS akımı ile IEC 60853 yük çevrimi semantiğini ayıran üretim geçişidir.

- Proje şeması: `0.16.4`
- Hesap/model dosyaları bu sürümün motor baseline'ıyla hash-kilitlidir.
- Hesap/model yayın hash kümesi: `ENGINE_BASELINE_v0.16.9.4.26.sha256`
- `load_current_a` ve fiziksel `current_override_a` doğrudan RMS akımdır; legacy `load_factor` steady-state akımı ölçeklemez.
- IEC 60853 `LF` ve kayıp-yük faktörü `μ` aktif yük-zaman profilinden tepe-normalize zaman integraliyle türetilir.
- Tam transient profil varken `μ` ikinci bir fizik çarpanı olarak uygulanmaz.
- FAZ 6.4 kuruma, FAZ 6.3 konstrüksiyon tabanlı Rac, FAZ 6.1/6.2 fiziksel kayıp vektörü, FAZ 4 geometri ve FAZ 5 procurement sözleşmeleri korunur.
