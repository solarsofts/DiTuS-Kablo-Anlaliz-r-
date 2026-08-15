# v0.16.9.3 — Kablo-Kanal Geometri Güvence Teknik Notları

## 1. Şablon ilkesi

Şablonlar `CableChannelTemplate` kayıtlarıdır. Uygulama sırasında fiziksel kablo ve devre kimlikleri korunur. Yalnız aşağıdaki tasarım alanları yeniden kurulur:

- kurulum tipi,
- parametrik kanal/hendek ölçüleri,
- duct slot listesi,
- kablo x ve derinlik koordinatları,
- duct slot atamaları,
- section kaynak referansı ve yerleşim etiketi.

Özel termal polygonlar ve harici ısı kaynakları korunur. Böylece kullanıcı verisi sessizce silinmez; ancak yeni geometriyle uyumu tekrar doğrulanır.

## 2. Fit ve açıklık matematiği

Kablo–kablo net açıklığı:

`c = d_center - (r_1 + r_2)`

Aynı çaplı kablolarda:

`c = d_center - D_cable`

Duct–duct net açıklığı:

`c = d_center - (D_out,1 + D_out,2)/2`

Kablo–duct radyal açıklığı:

`c_radial = (D_duct,inner - D_cable)/2`

Kanal/hendek zarf açıklığı; kablo veya duct merkezinin yüzey, taban ve eğimli yan sınıra en küçük mesafesinden nesne yarıçapı çıkarılarak hesaplanır.

Bu değerlerin fit sınırı sıfırdır. Uygulama özel minimum yapım mesafesi bu sürümde uydurulmaz.

## 3. Polygon topoloji kontrolü

Aktif termal malzeme polygonları için:

- en az üç geçerli köşe,
- pozitif alan,
- komşu olmayan kenarların kesişmemesi,
- geçerli malzeme kimliği

kontrol edilir. Self-intersection, hücre rasterizasyon sırasını fiziksel olarak belirsiz hale getirdiğinden hata olarak sınıflandırılır.

## 4. Ölçülendirme

İnşaat ölçüleri:

- alt/üst hendek genişliği,
- toplam derinlik,
- yatak, termal dolgu ve seçilmiş dolgu kalınlıkları,
- koruma plakası kotu,
- 1 m ölçek çubuğu.

Elektriksel ölçüler:

- her fiziksel kablonun yüzeyden merkez derinliği,
- x sırasındaki ardışık kablo merkezleri arası gerçek Öklid mesafesi.

Mühendislik çıktısında aktif ölçülendirme modu JSON metadata içine yazılır.

## 5. Sonuç bindirmeleri

2D termal gölge sonucu section/region anahtarıyla önbelleğe alınır. Geometri değişikliğinde önbellek geçersiz kılınır. Sonuç etiketi:

- `T`: nodal iletken sıcaklığı,
- `q`: kablo toplam ısı kaybı W/m

olarak gösterilir. Nodal kritik kablo ayrı vurgulanır.

## 6. Üretim motoru koruması

Bu sürüm:

- proje `lambda1` değerini yazmaz,
- IEC üretim ampacity sonucunu değiştirmez,
- üretim nodal sonucu değiştirmez,
- fiziksel motoru ana motor yapmaz,
- proje şemasını yükseltmez.
