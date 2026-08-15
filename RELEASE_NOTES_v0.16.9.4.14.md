# DiTuS Kablo Analizör v0.16.9.4.14

## Kurulum ekranı kontrol düzeltmeleri

- Parametre spinbox'larında üst ve alt oklar Kurulum ekranına özel geniş tıklama bölgeleriyle düzenlendi.
- Artış/azalış işlemi tek `singleStep` ile deterministik hale getirildi.
- Mouse wheel sayısal değeri değiştirmek yerine panel kaydırmasına bırakıldı.
- Kablo-Kanal kanvası wheel zoom katsayısı `%15` yerine `%8` yapıldı; hızlı touchpad akışında tek kontrollü adım uygulanır.

## Yayın temizliği

- Gerçek proje tabanlı bütün örnek, çıktı, test fixture'ı, rapor ve tarihsel regresyon kaydı kaldırıldı.
- Başlangıç ve demo akışları tamamen sentetik 20 km çift devre yeraltı hattına geçirildi.
- Sentetik hat 21 minör kesim ve 7 cross-bonding ana grubuyla, 1 km sınıfı makara sınırına uyumlu oluşturuldu.
- Paket ve dokümanlarda gerçek tesis/müşteri adı veya gerçek proje kaynağı bulunmaz.

## Hesap motoru sınırı

IEC 60287, bonding/CIM, nodal termal, transient, arıza/EPR ve SVL temel denklemleri değiştirilmedi. Yalnız proje gerilim düşümü girişinde eksik yerleşim-özel endüktans değerinin jenerik endüktansa güvenli fallback'i düzeltildi.
