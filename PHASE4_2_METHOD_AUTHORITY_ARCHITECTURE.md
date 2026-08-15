# FAZ 4.2 — Analitik–Nodal Yöntem Otoritesi

Analitik yürütme ile sonuç otoritesi ayrı kararlardır. `HOMOGENEOUS` fiziksel kesitte IEC analitik sonuç üretim otoritesi olabilir. `LAYERED` ve `COMPLEX_REGIONS` kesitlerde analitik sonuç engineering-preview/shadow evidence olarak korunur; nodal sonuç kalite kapısını geçtiğinde bağlayıcıdır. Legacy skaler geometri en fazla `DERIVED_FROM_SCALAR` yetkisindedir.

Nodal kalite kapıları yakınsama, enerji dengesi, lineer residual ve mesh-inceltme ampacity/sıcaklık farklarını kapsar. Katmanlı geometri nedeniyle analitik preview ile nodal farkı büyük olsa bile nodal üretim otoritesi kaybedilmez; fark shadow/review evidence olarak raporlanır. Model-kapsam indirimi region ERROR değildir.
