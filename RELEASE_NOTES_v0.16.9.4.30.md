# DiTuS Kablo Analizör v0.16.9.4.30

## FAZ 6.9 — Motor uygulanabilirliği

- Kablo fizik kapsamı için merkezi `model_applicability` kapısı eklendi.
- Tek damarlı, zırhsız kablo `SUPPORTED` üretim kapsamıdır.
- Çok damarlı kablo, IEC 60287 T1 geometrik faktör `G` uygulanmadığı için `REFERENCE_ONLY` olur.
- Zırhlı kablo, fiziksel zırh ağı uygulanmadığı ve lambda2 yalnız legacy katsayı olduğu için `REFERENCE_ONLY` olur.
- IEC 60287, global bonding/CIM, çok iletkenli EM, çok iletkenli termal, arıza/EPR ve IEC 60853 transient public girişlerinde headless fail-closed kapsam kontrolü eklendi.
- Engine precheck üretim motorlarında aynı kapsam kapısını HARD gate olarak gösterir.
- Rapor ve BOQ kapsam dışı kabloyu proje verisi olarak taşıyabilir; fizik motoru sonucu üretemez.
- Proje şeması değişmedi: 0.16.4.
