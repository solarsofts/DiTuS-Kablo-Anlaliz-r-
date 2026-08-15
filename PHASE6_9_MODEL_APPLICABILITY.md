# FAZ 6.9 — Motor Uygulanabilirliği

Sürüm: 0.16.9.4.30

## Tek doğruluk kaynağı
`ucd.calculations.model_applicability.evaluate_cable_model_applicability()` kablo yapısının üretim fizik motorlarına uygulanabilirliğini belirleyen tek kapıdır.

- `SUPPORTED`: tek damarlı ve zırhsız kablo. Mevcut IEC 60287, global bonding/CIM ve çok iletkenli elektrotermal üretim fiziği çalışabilir.
- `REFERENCE_ONLY`: çok damarlı ve/veya zırhlı kablo. Kayıt proje içinde tutulabilir; katalog/kaynak izlenebilirliği, rapor ve BOQ iş akışları kullanılabilir. Üretim fizik motoru çalıştırılamaz.
- `BLOCKED`: temel yapı tanımı fiziksel olarak geçersizdir (ör. kablo başına iletken sayısı < 1). Referans iş akışı da güvenli kabul edilmez.

## Neden çok damarlı kablo bloklanıyor?
Mevcut iç termal zincir eşdeğer konsantrik tek damarlı geometriye dayanır. Çok damarlı kablo için IEC 60287 T1 hesabında gerekli geometrik faktör `G` ve çok damarlı iç termal geometri uygulanmış değildir. `conductors_per_cable > 1` değerini mevcut formüle sokup sayı üretmek artık yasaktır.

## Neden zırhlı kablo bloklanıyor?
Mevcut `armour_loss_factor (lambda2)` bir legacy katsayıdır. Fiziksel zırh empedans/kayıp ağı çözülmediği için lambda2 bulunması zırhlı kabloyu üretim kapsamına sokmaz. ARMOUR/ZIRH katmanı veya pozitif lambda2, kabloyu `REFERENCE_ONLY` yapar.

## Fail-closed zincir
UI precheck ve headless API aynı politikayı kullanır. IEC 60287, global bonding/CIM, standalone çok-iletkenli EM ve çok-iletkenli termal giriş noktaları precheck atlanmış olsa bile kapsam dışı kabloda hata verir. Böylece UI dışı demo, regresyon veya otomasyon sessizce yanlış fizik çalıştıramaz.

## Bilerek izin verilenler
`REFERENCE_ONLY` kablolar katalog referans kıyasına, kaynak/veri yönetimine, raporlamaya ve BOQ/tedarik veri akışına girebilir. Bu sonuçlar fiziksel IEC rating veya bonding sonucu olarak etiketlenmemelidir.
