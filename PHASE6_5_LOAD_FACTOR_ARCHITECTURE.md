# FAZ 6.5 — Yük Faktörü ve IEC 60853 Kayıp-Yük Faktörü Mimarisi

## Kök hata

Eski kurulum veri modelinde `InstallationCircuitData.load_factor` ve `PhysicalCableData.load_factor`, bazı yardımcı/legacy hesap yollarında doğrudan RMS akıma çarpılıyordu. Bu davranış IEC 60287 kararlı durum tanımıyla uyumlu değildir: IEC 60287-1-1 sürekli sabit akım ve %100 yük faktörü koşulundaki rating/loss hesabıdır.

FAZ 6.1–6.2 üretim senaryo vektörü bu çarpanı zaten kullanmıyordu; FAZ 6.5 kalan legacy yolları da aynı sözleşmeye getirir ve IEC 60853 yük çevrimi terminolojisini ayrı bir fizik katmanına taşır.

## Bağlayıcı sözleşme

1. `load_current_a` ve `current_override_a` doğrudan RMS çalışma akımlarıdır.
2. Legacy `load_factor` alanları proje dosyası round-trip uyumluluğu için korunur; steady-state, bonding, global EM veya ampacity akımını ölçeklemez.
3. Unity dışı legacy alanlar kullanıcıya açık `IGNORED` uyarısı verir; sessiz fizik girdisi değildir.
4. IEC 60853 yük profili aktif fizik kaynağıdır.
5. Profil tepe akımına göre normalize edilen iki özet metrik türetilir:

   `LF = (1/T) integral I(t)/Ipeak dt`

   `mu = (1/T) integral [I(t)/Ipeak]^2 dt`

6. `mu`, kayıp-yük faktörüdür. Tam profil varken transient motor profilin kendisini çözer; `mu` ikinci kez kayıplara veya akıma uygulanmaz.
7. STEP profil integrali transient solver ile aynı sol-uç basamak semantiğini kullanır.
8. LINEAR profilde hem akım hem akım-karesi integrali parça parça analitik çözülür.
9. Yalnız `mu` bilinen fakat profil şekli bilinmeyen IEC 60853 kapalı-form yöntemi uygulanmaz; profil uydurulmaz.
10. `load_factor` artık fiziksel/geometrik fingerprint'e dahil değildir; kullanılmayan legacy alanın değişmesi yöntem/geometry doğrulamasını bayatlatmaz.

## Üretim yüzeyleri

- `resolved_physical_cables()` legacy faktörü uygulamaz.
- Kapalı çevrim ampacity temel devre akımları legacy faktörü uygulamaz.
- Global multiconductor production constraint yolu FAZ 6.1–6.2 davranışını korur.
- Geçici/çevrimsel çalışma alanı aktif profilden `LF`, `mu` ve tepe çarpanını gösterir.
- Proje raporu IEC 60853 özetinde bu üç metriği ayrı raporlar.
- Kablo-kanal düzeni ekranındaki legacy sütunlar read-only ve açıkça hesapta kullanılmadığı belirtilmiş alanlardır.

## Standart kapsam sınırı

Bu sürüm IEC 60853 terminolojisindeki loss-load factor `mu` değerini yük profilinden deterministik olarak türetir ve mevcut 2D transient sayısal çözüme izlenebilirlik metriği olarak ekler. Standardın yalnız `mu` ve sınırlı geçmiş yük bilgisiyle çalışan telifli kapalı-form cyclic-rating denklemlerinin bire bir uygulanması iddia edilmez.
