# Hesap Motoru Veri Kapıları ve Tasarım Hiyerarşisi

## Temel ilke

DiTuS bir motoru yalnız eksiksiz nihai veriyle çalıştırmaya zorlamaz. Ön tasarım ve aday eleme için koşullu hesap yapılabilir; fakat program aşağıdakileri birbirinden ayırır:

- motor çalışabilir mi,
- hangi varsayımlar kullanılacak,
- sonuç güncel mi,
- sonuç nihai tasarım için yeterli mi.

## Veri sahibinin tekliği

Bir girdi yalnız kendi editöründe tanımlanır. Hesap motorları aynı bilgiyi tekrar istemez.

| Veri grubu | Veri sahibi |
|---|---|
| Sistem gerilimi, frekans, yük, N-1 | Sistem/Yük |
| Chainage, güzergâh bölümleri | Güzergâh |
| Hendek, duct, toprak, backfill | Termal Güzergâh / Kesit |
| Kablo katmanları, Rdc, ekran geometrisi | Kablo Editörü |
| Joint, minor/major section, link box | Bonding Ağı |
| Arıza akımı ve temizleme süresi | Arıza Senaryoları |
| Topraklama/ECC/GCC | Bonding / Arıza |
| SVL aday ve yalıtım kriterleri | SVL |
| Yük-zaman profili ve ısı kapasiteleri | IEC 60853 |

## Hard ve soft gate

### HARD

Eksik olduğunda fiziksel denklem sistemi kurulamaz veya sonuç anlamsızdır. Motor bloke edilir.

### SOFT

Eksik olduğunda eşdeğer/varsayımsal veriyle ön hesap mümkündür. Kullanıcı açıkça onaylarsa motor çalışır; sonuç `CONDITIONAL` kalır.

## Motor bazlı özet

### İlk elektriksel ön eleme

HARD:
- sistem/yük,
- pozitif güzergâh uzunluğu.

SOFT:
- seçilmiş katalog adayı,
- değişmez snapshot,
- katalog/hesap R-L verisi.

### IEC 60287

HARD:
- tasarım akımı,
- kablo kesiti/dış çapı,
- termal bölgeler ve kesit şablonu,
- katman modeli veya T1-T3.

SOFT:
- doğrulanmış kablo kaynağı,
- doğrulanmış termal malzemeler,
- güncel bonding/λ1 sonucu.

### 2D nodal termal

HARD:
- 2D çözüm etkin termal kesit,
- malzeme kütüphanesi,
- kablo konumu/dış çapı,
- tasarım akımı.

SOFT:
- gerçek katman geometrisi,
- güvenilir malzeme özellikleri,
- güncel bonding kayıpları.

### Bonding / cross-bonding

HARD:
- akım ve frekans,
- minor/major section,
- joint/terminasyon düğümleri,
- cross bağlantı grafiği,
- metalik ekran elektriksel yolu ve etkin çap.

SOFT:
- ekran tel adedi/çapı,
- üretici doğrulanmış ekran verisi,
- ölçülmüş topraklama,
- bonding lead üretici empedansı.

### Arıza/EPR

HARD:
- etkin arıza senaryosu,
- arıza akımı,
- temizleme süresi,
- bonding/toprak ağı,
- ekran termik yolu,
- EPR dönüşü için topraklama.

SOFT:
- izlenebilir ölçüm/tasarım topraklama kaynağı,
- saha ECC/GCC doğrulaması.

### SVL

HARD:
- SVL adayları,
- fault-TOV ve süresi,
- joint/dış kılıf yalıtım seviyeleri.

SOFT:
- güncel bonding ve arıza sonuçları,
- üretici V-I/TOV/enerji eğrileri.

### IEC 60853

HARD:
- yük-zaman profili,
- kararlı durum termal taban,
- pozitif ısı kapasiteleri.

SOFT:
- güncel IEC 60287/2D sonucu,
- doğrulanmış hacimsel ısı kapasiteleri.

IEC 60853-3 toprak kuruması ve yeniden nemlenme henüz ayrı geliştirme kapsamındadır.
