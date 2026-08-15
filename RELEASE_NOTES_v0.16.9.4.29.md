# DiTuS Kablo Analizör v0.16.9.4.29

## FAZ 6.7 — Standing-voltage profili

Bu sürüm v0.16.9.4.28 tabanı üzerinde FAZ 6.7'yi kapatır.

Cross-bonded legacy/tanısal standing-voltage profili artık her minor section'ın açık-devre gerilim büyüklüğünü bağımsız çizmez. Bağlantı grafiğiyle çözülen A→B→C / B→C→A / C→A→B sheath yolları boyunca kompleks indüklenen EMF fazörleri kümülatif toplanır ve yalnız grounded major-section sınırında sıfırlanır. Dengesiz minor section uzunluklarında ara joint standing voltage böylece fiziksel fazör toplamını temsil eder.

PRIMITIVE_CIM ve NODE_VOLTAGE üretim çözümünde grafik profili legacy tahminden değil, çözülen sheath-to-earth düğüm gerilimlerinden üretilir. Böylece FAZ 6.6'da belirlenen global fizik ağı hem sayısal standing-voltage otoritesi hem de profil otoritesi olur.

Proje şeması değişmedi: 0.16.4.
