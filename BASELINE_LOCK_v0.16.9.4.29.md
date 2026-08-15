# Baseline Lock — v0.16.9.4.29

FAZ 6.7 kümülatif standing-voltage profili paketi.

- Taban: v0.16.9.4.28 (FAZ 6.6 global üretim bonding otoritesi korunur).
- CROSS_BONDED legacy/tanısal profilde her major section içindeki üç sheath yolu link-box bağlantı grafiğinden çözülür; minor EMF'leri kompleks fazör olarak yol boyunca kümülatif toplanır.
- Profil yalnız grounded major boundary'de sıfırlanır; her minor sonunda yanlışlıkla bağımsız |E_minor| gösterimi kaldırıldı.
- PRIMITIVE_CIM / NODE_VOLTAGE üretim profilinde kümülatif legacy tahmin yerine çözülmüş sheath-to-earth düğüm gerilimleri kullanılır.
- Legacy modlarda `max_standing_voltage_v`, yeni kümülatif profilin gerçek zarf maksimumundan türetilir.
- Proje şeması: 0.16.4.
