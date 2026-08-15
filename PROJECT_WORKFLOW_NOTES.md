# Proje Sihirbazı ve İlk Tasarım İterasyonu — Kilitli Akış

Bu dosya gerçek katalog ve saha verilerine geçildiğinde uygulanacak kullanıcı akışının yazılım karşılığıdır.

## Açılış

1. Yeni Kablo Sistemi Tasarla
2. Mevcut Tasarımı Kontrol Et
3. Projeyi Aç

## Beş adım

### 1. Sistem ve yük

Zorunlu başlangıç verileri:

- Nominal hat gerilimi
- Frekans
- Toplam ve aktif devre sayısı
- N-1 seçimi
- Şebeke topraklama tipi
- MW + güç faktörü, MVA veya A
- Gelecek büyüme ve tasarım marjı

Normal, N-1 ve marjlı tasarım akımları ayrı kayıtlardır.

### 2. Güzergâh

- DXF/DWG
- Kullanıcı çizimi
- Toplam uzunluk

CAD sonucu kullanıcı doğrulaması olmadan as-built veya hesap güzergâhı kabul edilmez.

### 3. İlk yerleşim

İlk aşamada yalnız kurulum profili, yaklaşık derinlik, faz/devre aralıkları, termal değer ve kaynağı, Cu/Al ve kablo/faz tercihi alınır.

### 4. Başlangıç kablosu

- Önerilen aday
- Katalog/manüel
- Kesitle hızlı başlangıç

Adaylar L1 seviyesindedir. Katalog satırı ve üretici konstrüksiyon bilgisi geldiğinde adayın değişmez proje snapshot'ı oluşturulur.

### 5. İlk birleşik hesap

- IEC 60287
- Metalik kılıf gerilimi
- Bonding tipi ve joint/link-box başlangıcı
- Primitive CIM/NV
- Arıza/EPR ve SVL için eksik veri kapısı

İleri veri başlangıç ekranında istenmez. Sonucu etkileyen eksik veri ilgili aşamada kullanıcıya sorulur.

## İlerleme durumları

```text
Sistem/Yük
Güzergâh
Kablo
Termal
Bonding
Arıza/EPR
SVL
Nihai Tasarım
```

Durumlar: `MISSING`, `PRELIMINARY`, `NOT_RUN`, `COMPLETE`, `CONDITIONAL`, `PASS`, `STALE`, `NOT_READY`.

## Nihai tasarım kapısı

L5 için en az:

- Üretici doğrulanmış kablo konstrüksiyonu
- Katalog/teklif revizyon izi
- Saha termal özdirenç ve dolgu kabul raporu
- Arıza akımları ve koruma temizleme süreleri
- Topraklama/EPR verileri
- Gerçek SVL eğrileri
- EMT doğrulaması
- As-built güzergâh ve aksesuar konumları

bulunmalıdır.
