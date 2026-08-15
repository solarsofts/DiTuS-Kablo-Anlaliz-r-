# Yönlendirilmiş İlk Tasarım ve Kablo Karar Akışı

## 1. Ana ayrım

DiTuS üç veri alanını birbirine karıştırmaz:

1. **Uygulama veri tabanı** — tekrar kullanılabilir standart ürünler ve malzemeler.
2. **Aktif proje** — güzergâh, kurulum, projeye atanmış kablo ve mühendislik kararları.
3. **Hesap sonuçları** — belirli bir proje girdi imzasıyla üretilmiş, güncel veya yeniden hesaplanması gereken sonuçlar.

Kablo veri tabanı proje ağacında gösterilmez. Proje ağacında yalnız aktif projeye atanmış kablolar yer alır.

Genel kablo veri tabanı kullanıcı uygulama-verisi klasöründe proje dosyalarından bağımsız saklanır. Projeye yalnız açıkça seçilip atanan ürün kaydı kopyalanır.

## 2. Kablo seçim yaşam döngüsü

```text
Veri tabanı kaydı
→ seçili ürün
→ projeye atanmış kablo
→ proje dosyasına kaydedilmiş kablo
→ hesaplarla doğrulanan tasarım kablosu
```

- **Seçim**, yalnız ekran seçimidir.
- **Projeye atama**, aktif proje modelini değiştirir.
- **Kaydet**, değişmiş proje dosyasını diske yazar.
- **Veri tabanına kayıt**, tekrar kullanılabilir genel ürünü oluşturur veya günceller.

Bu işlemler aynı düğme veya aynı durum olarak gösterilmez.

## 3. İlk tasarım iterasyonunun görevi

İlk tasarım iterasyonu bir karar destek adımıdır. Kabloyu sessizce seçmez ve projeye atamaz. Çıktısı:

- tasarım akımı,
- kaba aday listesi,
- önerilen aday,
- ön ampacity ve gerilim düşümü,
- eksik kurulum ve ürün verileri,
- kullanıcıdan beklenen sonraki karar.

İleri motorlar ancak kullanıcı kabloyu projeye atadıktan, kurulum/termal kesiti tanımladıktan ve ilgili hesap ön kontrolünden geçtikten sonra çalıştırılır.

## 4. Güzergâh giriş ilkesi

Hazır proje açıldığında program kullanıcıdan mevcut güzergâhı yeniden yazmasını istemez. Kaynakta bulunan bölümleri özetler ve şu iki eylemi sunar:

- Mevcut güzergâhı kabul et
- Eksikleri düzenle

Yeni bölüm ekleme ve düzenleme ayrı form ile yapılır. Özet tablo doğrudan hücre düzenleme amacı taşımaz.

## 5. Değişiklik etkisi

Projeye atanmış kablo değiştiğinde aşağıdaki sonuçlar yeniden hesaplanacak duruma geçer:

- elektriksel ön eleme ve gerilim düşümü,
- IEC 60287,
- 2D termal,
- bonding ve metalik kılıf kayıpları,
- arıza/EPR ve ekran dayanımı,
- SVL,
- IEC 60853,
- BOQ/BOM/RFQ.

Yalnız katalog açıklaması veya rapor notu değiştiğinde fiziksel hesaplar gereksiz yere geçersiz kılınmaz.

## 6. Kullanıcıya gösterilen durumlar

İçeride girdi hazırlığı, çalıştırma, güncellik ve olgunluk ayrı tutulur. Ana proje ağacı bunları yedi anlaşılır ifadeye indirger:

- Yapılacak
- Veri gerekli
- Hesaplanabilir
- Tamamlandı
- Koşullu
- Yeniden hesapla
- Bloke

Her durumun yanında kısa gerekçe ve tek sonraki işlem bulunur.
