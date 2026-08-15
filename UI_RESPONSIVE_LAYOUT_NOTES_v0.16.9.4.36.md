# Responsive pencere sözleşmesi — v0.16.9.4.37

1. Hiçbir üst düzey pencere `setFixedSize()` veya ekran boyutuna eşit
   `setMaximumSize()` ile kilitlenmez.
2. İlk normal geometri aktif monitörün görev çubuğu düşülmüş kullanılabilir alanına
   sığar.
3. Kullanıcı pencereyi büyütebilir, küçültebilir, maksimize edebilir ve monitörler
   arasında taşıyabilir.
4. Yardımcı diyaloglar yalnız ana pencere çağrı noktalarına güvenmez; global Show
   event filtresiyle aynı yerleşim otoritesine girer.
5. Büyük modül içeriği üst düzey pencereyi ekrandan dışarı büyütmez; StageHost
   gövdesi gerektiğinde scroll üretir ve gezinme footer'ı erişilebilir kalır.
6. Grafikler pencere büyütüldüğünde eski transformda küçük kalmaz. Termal görünüm
   kontrollü çizim sınırını viewport'a yeniden fit eder.
7. Termal alandaki görünürlük halo'su yalnız UI işaretidir; fiziksel kablo çapı ve
   hesap geometrisi değiştirilmez.
