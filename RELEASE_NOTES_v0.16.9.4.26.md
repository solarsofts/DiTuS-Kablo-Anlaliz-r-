# DiTuS Kablo Analizör v0.16.9.4.26

## FAZ 6.5 — load_factor semantiği

Bu sürüm v0.16.9.4.25 FAZ 6.4 tabanı üzerinde kararlı durum RMS akımı ile IEC 60853 çevrimsel yük terminolojisini ayırır.

- Devre ve fiziksel kablo legacy `load_factor` alanları steady-state akımını artık hiçbir üretim/legacy solver yolunda çarpmaz.
- `load_current_a` ve `current_override_a` doğrudan RMS çalışma akımıdır.
- Unity dışı legacy faktörler açık `LEGACY_*_LOAD_FACTOR_IGNORED` uyarısı üretir.
- Aktif transient yük profilinden tepe-normalize akım yük faktörü `LF` ve IEC 60853 kayıp-yük faktörü `mu` otomatik türetilir.
- STEP ve LINEAR profiller için zaman integralleri deterministik ve analitiktir.
- Tam yük profili mevcutsa transient motor profilin kendisini kullanır; `mu` ikinci bir kayıp/akım çarpanı değildir.
- Geçici Termal UI ve proje raporu `LF`, `mu` ve profil tepe çarpanını açık gösterir.
- Legacy `load_factor` fiziksel geometri fingerprint'inden çıkarılmıştır.
- Proje şeması 0.16.4 olarak korunmuştur.

Yalnız `mu` bilinen ancak yük-zaman şekli bilinmeyen IEC 60853 kapalı-form yöntemi bu sürümde uygulanmaz.
