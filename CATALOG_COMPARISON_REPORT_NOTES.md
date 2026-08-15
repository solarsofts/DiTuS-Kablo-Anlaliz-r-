# Katalog Teknik Karşılaştırma ve Doğrulama Raporu — Tasarım Notları

## Temel ilke

Üretici katalogları aynı koşulları kullanmayabilir. Toprak sıcaklığı, ısıl özdirenç, gömme derinliği, yük faktörü, faz düzeni ve kablo aralığı eşleşmeden katalog ampacity değerleri doğrudan büyüklük karşılaştırması için kullanılamaz.

Bu nedenle DiTuS iki ayrı bilgiyi gösterir:

1. **Katalogda yayımlanan referans değer**
2. **Gerçek projede tekrar hesaplanması gereken değer**

Katalog değeri hiçbir aşamada IEC 60287 veya 2D nodal sonuç alanına kopyalanmaz.

## Sıralama mantığı

Sıralama şu önceliklerle yapılır:

1. Ön elemede reddedilmemiş olma
2. Proje iterasyon kapılarının bloke olmaması
3. Bloke eksik veri sayısı
4. Üretici teyidi gereken alan sayısı
5. Mühendislik varsayımı sayısı
6. Katalog skaler veri kapsamı
7. Gerekli paralel kablo sayısı
8. Makul pozitif katalog marjına yakınlık
9. Ön gerilim düşümü

Bu sıralama bir maliyet optimizasyonu değildir. Fiyat, teslim süresi, minimum sipariş, makara boyu, montaj kabiliyeti ve ticari risk henüz puanlanmaz.

## Kaynak izlenebilirliği

Her adayda:

- üretici ve ürün serisi,
- katalog sayfası,
- kaynak kalite sınıfı,
- varsa katalog dosyası SHA-256,
- katalogda bulunan ve bulunmayan skaler alanlar,
- koşullu parametrik geometri kaynakları

gösterilir.

Katalogda yalnız toplam 35 mm² metalik ekran verilmişse tel sayısı ve tel çapı bilinmiyor kalır. Kablo dış çapı bilinse bile tüm iç katman çapları doğrulanmış sayılmaz.

## Çıktılar

- JSON: makinece okunabilir tam sonuç ve hesap izi
- Markdown: gözden geçirme ve sürüm kontrolü
- HTML: harici bağımlılığı olmayan okunabilir teknik rapor

PDF üretimi bu sürümün kapsamında değildir. Nihai teknik rapor motorunda kontrollü şablon ve sayfa düzeniyle ayrıca ele alınacaktır.
