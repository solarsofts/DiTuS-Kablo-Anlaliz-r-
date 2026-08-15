# Kablo-Kanal Düzeni — Devre Paneli ve Hat Aralığı Hotfix Notları

## Problem

Kablo-Kanal Düzeni sağ panelindeki parametre alanı dikey splitter'ın büyük bölümünü işgal ediyor, Devre Yerleşimi sekmesi ilk açılışta alt sınırda kalıyordu. Ayrıca `Paralel grup merkez aralığı` ve `Duct sütun` alanları koşulsuz göründüğü için farklı devre/hat mesafesiyle karıştırılıyordu.

## Çözüm

### Panel görünürlüğü

- Alt panel minimum 300 px yüksekliğe alındı.
- Parametre panelinin minimum yüksekliği azaltıldı.
- Splitter ilk açılışta yaklaşık yarı yarıya kurulur.
- `Devre Yerleşimini Aç` kontrolü alt paneli açar ve ilgili sekmeyi seçer.

### Bağımsız hat aralıkları

Tablo sırasındaki devreler için komşu merkez aralıkları sağlanabilir:

```text
C1-C2; C2-C3; C3-C4 ...
```

Örnek giriş:

```text
0,80; 0,70; 1,00
```

İlk devrenin mevcut X merkezi ankraj kabul edilir. Sonraki X merkezleri kümülatif hesaplanır. Veri modeli değişmemiştir; sonuçlar mevcut `PhysicalCableData.x_m` alanlarına uygulanır.

### Alan anlamları

- **Devre merkez aralığı:** ortak otomatik yerleşimde bütün komşu devreler için tek eşit aralık.
- **X merkezi:** her devrenin bağımsız yatay konumu.
- **Komşu hat merkez aralıkları:** tablo sırasındaki farklı C1-C2, C2-C3 vb. mesafeler.
- **Paralel grup merkez aralığı:** aynı fazda birden fazla paralel kablo grubunun aralığı; farklı devrelerin aralığı değildir.
- **Duct sütun:** yalnız duct ızgarasındaki sütun sayısıdır; devre mesafesi değildir.

## Kapsam sınırı

Bu hotfix yalnız kesit ekranı UI davranışıdır. Hesap algoritmaları, model denklemleri ve üretim sonucu yolları değişmemiştir.
