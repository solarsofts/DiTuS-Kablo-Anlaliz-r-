# Proje Kablo Uygulama ve Veri Kapıları Tasarım Notu

## Amaç

Katalog aday seçimi ile fiziksel proje hesabı arasındaki boşluğu kapatmak. Bir katalog satırının projeye atanması; yalnız ürün adını kopyalamak değil, kullanılan veriyi, güzergâh kapsamını, eksikleri ve kaynak kararlarını değişmez biçimde kaydetmektir.

## Veri modeli

`CableApplicationData` şu kayıtları taşır:

- seçilen aday ve katalog kayıt ID'si,
- uygulanan snapshot ID ve SHA-256,
- güzergâh bölümü bazında kablo atamaları,
- veri tamamlama maddeleri,
- kaynak çelişkisi kararları,
- son iterasyon kapısı durumu ve hesap izi.

`RouteCableAssignment`, seçilmeyen bölümleri silmez. Her bölüm için aktif/pasif atama kaydı tutulur. v0.15.1 hesap çekirdeğinde proje kablosu hâlâ tek ortak kablo modelidir; farklı güzergâh bölümlerinde farklı kablo tipleri kullanılması sonraki çoklu-kablo güzergâh modelidir.

## Snapshot ilkesi

Katalog kaydı önce proje kablosuna kopyalanır. Ardından:

- kablo/faz sayısı,
- proje gerilimi,
- frekans,
- kablo başına tasarım akımı

uygulanır ve snapshot yeniden SHA-256 ile imzalanır. Hesaplar harici katalog satırına değil bu snapshot'a bağlıdır.

## Veri yeterliliği

`MISSING` yalnız değer gerçekten yoksa bloke eder. Değer mevcut fakat üretici teyidi veya mühendislik varsayımı durumundaysa ön hesap çalışabilir; sonuç `CONDITIONAL` kalır.

Örnek:

- Dış çap katalogda mevcut: `CATALOG_AVAILABLE`
- İletken çapı nominal kesitten eşdeğer daire olarak üretildi: `MANUFACTURER_CONFIRMATION_REQUIRED`
- İzolasyon katman çapı parametrik görünüm için varsayıldı: `MANUFACTURER_CONFIRMATION_REQUIRED`
- Ekran tel adedi/çapı yok: değer üretilmez
- Kablo katman ısı kapasitesi yok: IEC 60853 nihai doğrulaması koşullu

## Kaynak kararları

`SourceConflictDecision` kaynak dokümanı değiştirmez. Karar zamanı, karar veren, gerekçe, seçilen kaynak ID'leri ve çözümlenmiş değer ayrı tutulur.

Uygulanabilen doğrudan kararlar:

- güç faktörü,
- güzergâh fiziksel uzunluğu.

Pozitif-sıra R/X kayıtları, kablo Rdc veya IEC 60287 malzeme parametresiyle aynı büyüklük olmadığı için otomatik eşlenmez.

## İterasyon kapıları

Bloke eden kapılar:

1. Snapshot yok
2. Zorunlu temel kablo verisi yok
3. Kritik/yüksek kaynak çelişkisi kararsız
4. Aktif güzergâh ataması yok

Gerilim düşümü ön hesabı katalog R/L verisiyle yapılır ve nihai yük akışı sonucu değildir.

## Bilinen sınır

- Bölüm bazında farklı kablo snapshot'ları henüz aynı projede birlikte çözülmez.
- Veri tamamlama sihirbazı kullanıcı girdisini kaynak kaydı olarak ayrıntılı düzenleme ekranına yönlendirir; üretici PDF'sinden otomatik kesin veri kabulü yoktur.
- İterasyon kapısı fiziksel model doğrulaması değildir; hangi hesapların hangi güven seviyesinde çalışabileceğini denetler.
