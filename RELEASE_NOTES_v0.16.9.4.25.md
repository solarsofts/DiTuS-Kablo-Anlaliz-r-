# DiTuS Kablo Analizör v0.16.9.4.25 — FAZ 6.4 Toprak Kuruması

- IEC kritik-izoterm/toprak kuruması üretim zinciri eklendi.
- `ThermalMaterialData` içinde zaten bulunan kritik kuruma sıcaklığı ve kuru-durum ısıl özdirenci artık hesap motorları tarafından tüketiliyor.
- Basit tek izole doğrudan-gömülü kablo için IEC iki-bölge analitik kuruma hesabı eklendi.
- Çok kablolu/karşılıklı ısıtmalı gerçek x-y geometrilerde analitik kuruma genellemesi yapılmıyor; üretim `AUTO` nodal kritik-izoterm çözüme geçiyor.
- Nodal çözücü malzeme bazlı kritik sıcaklık/kuru rho ile hücreleri iteratif olarak kuru duruma geçiriyor; yeraltı su seviyesinde/altındaki hücreler kurutulmuyor.
- Kuruma yakınsaması nodal kalite ve kapalı elektro-termal çevrim yakınsama kapısına bağlandı.
- `ANALYTIC_DRYOUT_REQUIRES_NODAL` model-kapsam hatası fiziksel ret değildir.
- Kuruma etkin ve nodal üretim başarılı olduğunda analitik IEC yolunun kapsam dışı olması workflow tarafından toplam hesap çökmesi olarak işaretlenmiyor.
- Üretim ve nodal rapor tablolarına termal yöntem, kuruma malzemeleri, kuru hücre fraksiyonu ve kuruma yakınsaması eklendi.
- Proje şeması `0.16.4` değişmedi.
