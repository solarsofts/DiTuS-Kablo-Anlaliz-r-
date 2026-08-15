# Tam-Tuval Ana Ekran ve Ayrı Modül Pencereleri

## Tasarım ilkesi

Ana pencere bir form ve sonuç deposu değil, projenin mekânsal çalışma alanıdır. Kullanıcı ana pencerede güzergâhı, CAD altlığını ve proje ağacını görür. Ayrıntılı tanım ve sonuçlar yalnız ihtiyaç halinde açılır.

## Ana pencere sözleşmesi

- Sol: proje ağacı ve renkli tasarım akışı
- Orta: güzergâh / Plan-CAD tuvali
- Sağ: kalıcı panel yok
- Alt: kalıcı sonuç bloğu yok
- Üst: kısa ve sık kullanılan işlemler

## Yönlendirme

Aşama düğmeleri yerine proje ağacı tek navigasyon kaynağıdır. Renk, metin ve tooltip birlikte kullanılır; renk tek başına bilgi taşımaz. Tooltip en fazla şu bilgileri gösterir:

1. aşama adı ve durumu,
2. eksik girdiler,
3. bloke nedenleri,
4. önerilen sonraki işlem.

## Ayrı pencere davranışı

### Proje Modülü

Proje ağacındaki bir aşama veya nesne seçildiğinde ilgili editör açılır. Pencere kapatıldığında ana güzergâh görünümü değişmez.

### Sonuçlar ve Kayıtlar

Hesap çalıştırıldığında ilgili sonuç sekmesi ayrı pencerede açılır. Sonuçlar ayrıca proje ağacındaki `Sonuçlar ve Kayıtlar` grubundan erişilir.

### Rehber ve Nesne Bilgileri

Varsayılan kapalıdır. Menüden veya gerekli durumda açılır. Ana pencerede kalıcı sağ panel oluşturmaz.

## İterasyon yöntemi

Bu düzen saha/masaüstü kullanımında kullanıcı geri bildirimiyle iteratif geliştirilecektir. Sonraki v0.16.3 sürümünde Kablo, Termal Kesit, Joint/Termination, Link Box ve SVL editörlerinin içerikleri ayrı pencere mantığına göre ayrıca sadeleştirilecektir.
