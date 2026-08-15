# v0.16.9.4 — Kablo-Kanal Düzeni UX / Debug Teknik Notları

## Kök nedenler

### İlk açılışta kabloların çok küçük görünmesi

Önceki sürüm `scene.itemsBoundingRect()` kullandığı için 1240×780 sayfa arka planı, başlıklar, ölçüler, lejant ve uzaktaki sarı tutamaçlar fit hesabına giriyordu. Yeni sürüm yalnız mühendislik nesnelerinin metre tabanlı zarfını hesaplar:

- hendek/kanal polygonu,
- fiziksel kablolar,
- duct slotları,
- harici ısı kaynakları,
- özel malzeme polygonları.

### Tıklama/sürükleme sırasında çökme veya zoom-out

Geometri tutamacının `ItemPositionHasChanged` olayı doğrudan tüm sahneyi yeniden çiziyordu. Bu sırada hareket eden grafik nesnesi sahneden silinebiliyordu. Yeni sürüm yeniden çizimi olay döngüsünün sonuna erteler ve tekrarlanan çağrıları tek çağrıda birleştirir.

### TREFOIL seçiminin FLAT kalması

İki farklı seçim alanı kullanıcıda aynı beklentiyi oluşturuyordu:

1. Section şablonu: yalnız uygulama düğmesiyle yazılır.
2. Sağ panel formasyon seçimi: önceki sürümde yalnız hazır yerleşim düğmesiyle etkiliydi.

Yeni davranış:

- Section şablonu listesi boş başlangıç satırıyla açılır ve seçimin tek başına uygulanmadığını açıkça belirtir.
- Sağ panelde TREFOIL/FLAT/VERTICAL seçimi mevcut kabloların x-y yerleşimine anında uygulanır.

## Çakışmasız pitch mantığı

Kablo dış çapı `D`, görsel/kurulum güvenlik payı `c` olmak üzere:

- Faz merkezi alt sınırı: `s_phase >= D + c`
- Paralel formasyon pitch'i: `p_parallel >= formation_width + D + c`
- Devre pitch'i: `p_circuit >= circuit_footprint + D + c`

Bu değerler nihai proje minimum yapım aralığı değildir. Yalnız çizimde fiziksel kablo zarflarının üst üste binmesini önleyen geometri kapısıdır.

## Görsel katman sırası

1. Hava / yüzey arka planı
2. Doğal zemin ve hafif zemin taraması
3. Hendek temel dolgusu
4. Seçilmiş dolgu
5. Termal backfill + çapraz tarama
6. Yataklama
7. Duct / beton kanal / HDD / tünel elemanları
8. Koruma plakası
9. Formasyon kılavuzu
10. Fiziksel kablolar ve isteğe bağlı ID etiketleri
11. Ölçüler, tutamaçlar ve sonuç etiketleri

## Hesap bağlantısı

Bu sürüm yalnız geometri üretimi ve arayüz davranışını düzeltir. Kontur için mevcut gölge termal motor çağrısı korunmuştur. Üretim hesap motorlarına yeni bağlantı veya sonuç yazma işlemi eklenmemiştir.
