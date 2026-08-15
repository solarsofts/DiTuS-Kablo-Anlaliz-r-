# Standart ve Hesap Kapsamı — v0.16.6

## IEC 60287

Aktif çekirdek; iletken AC direnci, dielektrik kayıp, T1–T4 termal dirençleri, metalik kılıf/zırh kayıp faktörleri, sürekli ampacity ve tasarım yükündeki iletken sıcaklığını hesaplar.

v0.16.9.4.34 itibarıyla global bonding ağının boyuna metalik kılıf `I²R` oranı toplam IEC `λ1` olarak etiketlenmez. Rating zinciri desteklenen tekli-devre Trefoil/Flat koşullarında IEC 60287-1-1 §2.3.6.1 `λ1″` eddy-current bileşenini ayrı hesaplar; Milliken kolunda §2.3.5 `F` uygulanır. Note 3 konstrüksiyonu açıkça kanıtlanmışsa eddy terimi kaynaklandırılmış biçimde ihmal edilir. CUSTOM veya paralel/çok-devre kesitte otomatik kapalı form genişletilmez; doğrulanmış dış `λ1″` yoksa üretim ampacity fail-closed bloke edilir. Solid both-end non-Milliken kol, §2.3 giriş kapsamına göre ek `λ1″` istemez.

Her chainage bazlı termal bölge ayrı IEC 60287 bölümüne dönüştürülür. Güzergâh kapasitesi en düşük bölgesel ampacity ile sınırlandırılır. `AUTO_MIXED_ZONE` analitik karışık-zemin yaklaşımı, 2D solver için karşılaştırma sonucu olarak korunur.

FAZ 6.4 ile kararlı durum kısmi toprak kuruması ayrıca çözülür. Basit tek izole doğrudan-gömülü kabloda IEC iki-bölge kritik-izoterm bağıntısı kullanılabilir. Çok kablolu/karşılıklı ısıtmalı gerçek x-y geometrilerde aynı basit formül genellenmez; malzeme bazlı kritik izoterm/kuru ısıl özdirenç kullanan doğrusal olmayan nodal çözüm üretim otoritesidir.

## IEC 60287-2-1 / termal direnç

- İç T1–T3: eşdeğer konsantrik katman veya manuel değer
- Homojen toprak T4: image-method matris yaklaşımı
- Karışık doğal zemin/termal dolgu T4: eşdeğer yarıçaplı analitik ön model
- Duct bank/HDD: kaynak gösterilen manuel T4 ile IEC karşılaştırması

Bu analitik modeller 2D çözümün yerine geçmez; iki sonuç birlikte raporlanır.

## 2D kararlı durum termal çözüm

Bağımsız hücre-merkezli sonlu hacim çözümü, ısı iletim denklemini proje geometrisi ve malzeme verileriyle sayısal olarak çözer.

Kapsam:

- Çok malzemeli hendek ve yüzey geometrisi
- Duct/grout eşdeğer 2D kesiti
- Yeraltı suyu altı iletkenlik düzeltmesi
- Birden fazla aktif devre ve paralel kablo/faz
- Kablo kayıplarının sıcaklığa bağlı iterasyonu
- Malzeme bazlı kritik-izoterm toprak kuruması ve kuru-durum ısıl özdirenci
- Yeraltı su seviyesinde/altında kuruma maskesi engeli
- Kararlı durum ampacity
- Enerji dengesi ve mesh duyarlılığı

Duct içi konveksiyon/radyasyon, eşdeğer malzeme ile temsil edilir. Akışkanlar dinamiği çözülmez.

## IEC 60853-2 iş akışı

IEC 60853-2'nin kapsamı; 18/30 (36) kV üzerindeki kablolar için cyclic rating ve tüm gerilim seviyelerindeki kablolar için emergency rating hesaplarını içerir. v0.13 aşağıdaki iş akışını uygular:

- Kullanıcı tanımlı yük-zaman çevrimi
- Hacimsel ısı kapasitesiyle 2D transient conduction
- Çevrimsel başlangıç ön koşullandırması
- Profil altındaki sıcaklık-zaman çözümü
- Normal sıcaklık limitine göre çevrimsel rating
- Kullanıcı tanımlı süre ve acil sıcaklık limitine göre emergency rating
- Güzergâhın en düşük bölgesel rating ile sınırlandırılması

Uygulanan yöntem, IEC 60853 terminolojisini ve tasarım akışını izleyen bağımsız sayısal sonlu hacim çözümüdür. Standardın telifli kapalı-form denklemlerinin bire bir normatif yeniden üretimi değildir.

## FAZ 6.5 — Yük faktörü / kayıp-yük faktörü

IEC 60287-1-1 kararlı durum akım taşıma kapasitesini %100 yük faktörü ve sürekli sabit akım koşulu için tanımlar. Bu nedenle kurulum modelindeki legacy `load_factor` alanları artık RMS akımı küçültmez. IEC 60853 transient/cyclic çalışmasında aktif yük-zaman profilinden tepe akıma göre normalize edilmiş ortalama akım faktörü `LF` ve kayıp-yük faktörü `μ = average[(I/Ipeak)^2]` otomatik türetilir. Tam profil mevcut olduğunda sayısal transient motor profilin kendisini çözer; `μ` ikinci bir akım/kayıp çarpanı olarak uygulanmaz. Yalnız `μ` bilinen fakat yük çevrimi şekli bilinmeyen kapalı-form IEC 60853 yöntemi bu sürümün kapsamı dışındadır.

## IEC 60853-3

Kararlı durum kritik-izoterm kuruma modeli FAZ 6.4 kapsamında uygulanmıştır; bu, IEC 60853-3'ün zamana bağlı cyclic dry-out/rewetting ve nem göçü modelinin uygulandığı anlamına gelmez. Zaman bağımlı kuruma, yeniden ıslanma ve nem taşınımı bu sürümde çözülmez.

## IEEE 575 / CIGRE TB 797

Explicit sheath cross-bond grafiği, primitive iletken/metalik-kılıf/GCC ağı, CIM/MNA ve Node-Voltage çözümü korunur. Bonding metal kayıpları mümkün olduğunda termal bölgelere chainage örtüşmesiyle dağıtılır ve 2D kararlı/geçici ısı kaynaklarına eklenir.

Toprak dönüşü `SIMPLIFIED_CARSON` ön modelidir. Tam Pollaczek/Wedepohl–Wilcox/Ametani ve yayımlanmış referans vakalarla kapsamlı regresyon doğrulaması tamamlanmamıştır.

## Arıza / EPR / SVL

Üç faz, faz-faz ve tek faz-toprak power-frequency senaryoları; metalik-kılıf/GCC/toprak akım paylaşımı, EPR, sheath-ground ve interrupt gerilimleri hesaplanır. SVL katmanı MCOV, TOV, residual voltage, bonding-lead katkısı, enerji ve deşarj akımı ön kontrollerini yapar.

Frequency-dependent EMT ve nonlinear MOV enerji integrasyonu henüz yoktur.

## Veri olgunluğu

Termal veriler `DESIGN`, `TESTED` ve `AS_BUILT` olarak ayrılır. Ön varsayımlar otomatik uyarı üretir. Hacimsel ısı kapasitesi girilmemiş malzemelerde kategori varsayımı kullanılır ve trace/uyarı kaydı oluşturulur.

## Doğrulama durumu

İç otomatik testler fiziksel yön, enerji dengesi, mesh yakınsaması, yük artışı, ısı kapasitesi etkisi, emergency duration etkisi, migration ve hesap zincirini kontrol eder. Bunlar yayımlanmış IEC 60853 referans vakalarıyla bağımsız doğrulamanın yerine geçmez.

## Kullanım sınırı

v0.13 sonuçları ön mühendislik ve yazılım geliştirme amaçlıdır. Üretici doğrulanmış kablo verileri, gerçek yük profili, saha/laboratuvar termal ölçümleri, gerçek zemin ısı kapasitesi ve nem verileri, bağımsız teknik gözden geçirme ve benchmark doğrulaması olmadan nihai kablo sistemi tasarımı olarak kullanılmamalıdır.


## v0.13.1 arayüz ve optimizasyon kapsamı

- Hesap standardı kapsamı değiştirilmeden termal sonuçlar tek seçim/tek ayrıntı penceresi mimarisine taşındı.
- Bölgesel tasarım alternatifleri, seçili 2D nodal modelin gerçek yeniden çözümüyle karşılaştırılır.
- Bu öneriler normatif otomatik tasarım onayı değildir; mekanik, inşaat, elektromanyetik ve maliyet kontrolleri ayrıca gereklidir.
- Duct/grout termal özdirenci bölge veya şablon bazında açık override olarak tutulabilir; sıfır değer malzeme kütüphanesindeki değerin kullanılacağı anlamına gelir.

## v0.14 — Kablo konstrüksiyonu ve katalog veri katmanı

- IEC 60287, bonding, arıza ve termal motorların ortak kablo geometrisi parametric layer stack üzerinden üretilebilir.
- Katalog, üretici çizimi, test raporu, standart türevi, hesaplanan ve kullanıcı varsayımı değerleri ayrı kaynak tipleridir.
- Kablo gerilim sınıfı ve uygulanabilir standart kullanıcı/üretici kaydıdır; yazılım yalnız sistem geriliminden nihai uygunluk kararı vermez.
- Konstrüksiyon doğrulaması normatif tip/ön yeterlilik değerlendirmesinin yerine geçmez.
- Katalog ampacity değerleri yalnız referans koşulları proje koşullarıyla eşleşirse benchmark olarak kullanılacaktır.
- Jenerik v0.14 katalog paketleri üretici ürünü veya satın alma verisi değildir.

## v0.14.1 — Yayın veri bütünlüğü denetimi

- Yayın paketindeki regresyon ve demo akışları yalnız tamamen sentetik 20 km yeraltı hat örneğini kullanır.
- Yayın veri bütünlüğü denetimi normatif bir standart çözümü değildir; veri soy ağacı, çelişki ve eksik veri kapısıdır.
- Havai hat kapsam dışıdır. Bara kısa devre değerleri yalnız yeraltı modelinin sınır/benchmark girdisi olarak kullanılır.
- Parametrik 36 kV 400/35 katman geometrisi üretici verisi değildir ve `CONDITIONAL` olarak tutulur.

## v0.16.3 — Fiziksel kurulum ve kesit veri katmanı

v0.16.3 her fiziksel kabloyu devre/faz/paralel numarası ve metre cinsinden gerçek x-derinlik koordinatıyla ayrı proje nesnesi olarak saklar. Çoklu devre, paralel kablo/faz, faz sırası, duct slotu, farklı devre yükleri ve harici ısı kaynakları ortak kesit modelinde tanımlanabilir.

Bu sürüm bir standart hesap genişlemesi değil, kontrollü veri altyapısı sürümüdür. `solver_coupling_mode=DESIGN_ONLY` kaldığı sürece mevcut IEC 60287, bonding, 2D nodal ve IEC 60853 sonuçları yeni kesitten otomatik yeniden çözülmez.

### IEC 60287-1-2:2023

Çift devre düz formasyonda tek damarlı kabloların metalik kılıf girdap kayıpları ve bonding durumlarına ilişkin kapsam, gerçek fiziksel yerleşimin kaydedilmesini gerektirir. Her iki uçtan bağlı kılıflardaki dolaşım kayıpları IEC 60287-1-3 kapsamıyla birlikte ele alınacaktır.

### IEC 60287-1-3:2023

Her faz için herhangi sayıda paralel tek damarlı kablonun herhangi fiziksel düzende akım paylaşımı ve dolaşım kayıpları kapsamındadır. v0.16.3 bu genel N-kablo modelinin girdisini oluşturur; eşitsiz akım paylaşımı çözümü henüz uygulanmamıştır.

### IEEE 575-2014 / P575

IEEE 575-2014, 27 Mart 2025 itibarıyla `Inactive-Reserved` durumundadır. Aktif revizyon çalışması P575'tir. Mevcut tek-devre faz bazlı EMF ve bonding ön modelleri korunur; v0.16.3 çoklu fiziksel kablo veri katmanını ekler, IEEE 575/P575 uyumlu genel ağ çözümünü tamamlamaz.

### CIGRE TB 797

Projeye özgü kablo, kurulum, sistem ve bonding parametreleriyle indüklenen gerilim/akım değerlendirmesi için ortak fiziksel kurulum modeli hazırlanmıştır. Tam Pollaczek/Wedepohl-Wilcox/Ametani ve yayımlanmış çok iletkenli benchmark doğrulaması kapsam dışıdır.

### IEC 60853-3:2002 sıra kararı

Kısmi toprak kuruması altında cyclic rating çözümüne geçiş ertelenmiştir. Önce çoklu kablo kayıpları, ortak kararlı sıcaklık alanı ve kablo bazlı başlangıç sıcaklıkları doğrulanacaktır. IEC 60853-3'ün grup aralığı ve özel backfill uygulama sınırları ayrıca kontrol edilecektir.


## v0.16.6 gerçek x-y çoklu kablo termal gölge kapsamı

- IEC 60287-1-3 yönelimli global core akım paylaşımı ve kılıf ağı sonuçları termal bölgelere aktarılır.
- Her fiziksel kablo için farklı core/kılıf/dielektrik/zırh kaybı ve gerçek x-y koordinatı kullanılır.
- Analitik self/mutual image matrisi ile ortak 2D sonlu-hacim alanı bağımsız karşılaştırma üretir.
- Harici doğrusal ısı kaynakları gerçek koordinatından hesaba katılabilir.
- Bu yol `SHADOW_COMPARE` durumundadır; üretim IEC/nodal rating, proje `lambda1` veya uygunluk kararını değiştirmez.
- Elektro-termal geri besleme, gerçek x-y proximity genellemesi, fiziksel zırh ağı ve yayımlanmış TB 880 tam benchmark seti henüz tamamlanmamıştır.

## v0.16.8 doğrulama ve motor yükseltme kapısı

Fiziksel N-core/N-kılıf elektro-termal motorun `PHYSICAL_PRIMARY` yapılması otomatik değildir. v0.16.8 şu kanıtları ayrı kapılarda izler:

- GLOBAL_DIRECT_KKT ↔ GLOBAL_SHEATH_SCHUR anlaşması,
- devre/faz akım toplamı, metallic-network KCL ve dal gerilim residual'ları,
- 2D termal yakınsama, enerji kapanışı ve lineer residual,
- kablo fiziksel parametre kapsamı ve kaynak kökeni,
- IEC 60287-1-1, IEC 60287-1-3, CIGRE TB 797 ve CIGRE TB 880 harici doğrulama kanıtları.

Lisanslı/yayımlanmış sayısal vaka verileri pakete kopyalanmaz. İzlenebilir dış benchmark kanıtları tamamlanmadığında motor `HOLD_SHADOW` durumunda kalır.

## FAZ 2 katalog ve parametrik geometri sınırı — v0.16.9.4.17

- Açık kaynak dağıtımda üretici katalog satırları ve katalog PDF'leri paketlenmez.
- IEC 60228, IEC 60502-2, HD 620 S3, IEC 60840 ve IEC 60287-2-1 sayısal tablolarının lisanslı kaynaklardan nihai transkripsiyonu ayrı kontrollü veri çalışmasıdır.
- Paketlenmiş profil sayıları `PENDING_LICENSED_STANDARD_TABLE_REVIEW` durumundadır; bu nedenle bütün jenerik şablonlar `CONDITIONAL` kalır.
- Yarı iletken, bant, sıkıştırma ve YG metalik sheath geometrileri standart tarafından tek nominal değerle verilmediği sürece `USER_ASSUMPTION` sınıfındadır.
- Üretici tarafından yayımlanmış dış çap ve kg/km, parametrik katman geometrisini değiştirmez; yalnız çap ve kütle doğrulama kapılarında CAT kanıtı olarak kullanılır.
- FAZ 2 değişikliği çözüm denklemlerini değiştirmez; katalog oluşturma, senkronizasyon, kaynak izi ve örnek veri üretimiyle sınırlıdır.

## FAZ 3.1 IEC termal çalışma sıcaklığı ve kısmi güzergâh sonucu — v0.16.9.4.18

- IEC 60228'deki 20 °C, iletken DC direncinin referans sıcaklığı olarak ele alınır; çalışma sıcaklığının alt sınırı olarak uygulanmaz.
- `Rθ = R20 · [1 + α20(θ-20)]` düzeltmesi, seçili malzeme profiliyle fiziksel/matematiksel geçerlilik kapıları altında kullanılır.
- Cu, Al, Pb/kurşun ve bronz malzeme ρ20/α20 çözümü ortaklaştırılmıştır. Açık kullanıcı override'ı korunur; eski Al kayıtlarındaki tarihsel `0.00393` otomatik varsayımı malzeme profiline göç eder.
- `delta_theta <= 0`, dielektrik kaybın izin verilen artışı tüketmesi ve termal kararsızlık paydasının pozitif olmaması, verilen girdiler için kararlı durum çözümünün bulunmadığını gösteren fiziksel ret kapılarıdır; kaldırılmamıştır.
- Güzergâh uygunluğu yalnız tam çözülen gerekli senaryolarda kesin `UYGUN` olabilir. Kısmi çözümde resmi ampacity üretilmez; çözülen bölgelerin minimumu yalnız gerçek ampacity için üst sınırdır.
- Kısmi sonuçta çözülen bir bölümün yetersizliği veya fiziksel ret kapısı kesin yetersizlik kanıtı olabilir. Bu hüküm kablo veri olgunluğu (`DRAFT`, `CONDITIONAL`, `VERIFIED`) ile birlikte raporlanır.
- VERTICAL/DUCT analitik yerleşim modeli, bonding kılıf sıcaklığı alt sınırı ve sıfır akım bonding yolu bu fazın kapsamı değildir.

## FAZ 6.8 katalog referans ampacity normalizasyonu — v0.16.9.4.27

- IEC 60287-3-1 katalog/üretici rating'inin yayımlandığı site/referans koşullarından ayrılmaması gerektiği kabulüyle, katalog `Iref` değeri artık proje rating'i olarak doğrudan kullanılmaz.
- Paket içinde lisanslı IEC, ulusal veya üretici düzeltme tablolarının sayısal satırları gömülmez. Düzeltme faktörü ancak kullanıcı tarafından açık `factor`, `reference_value`, `target_value`, `source_type` ve `source_reference` ile girildiğinde tüketilir.
- Referans ve proje koşulu aynıysa ilgili faktör `1.0` kabul edilir. Farklıysa otomatik interpolasyon/tahmin yapılmaz; exact hedef için kaynaklı faktör yoksa normalizasyon `REFERENCE_ONLY_INCOMPLETE` kalır.
- Toprak sıcaklığı, gömülme derinliği, toprak ısıl özdirenci, kurulum yöntemi, formasyon ve paralel kablo/gruplama ayrı dönüşüm boyutlarıdır. Güzergâh birden fazla bölge içeriyorsa her bölüm ayrı normalize edilir; normalize katalog benchmark'ının governing değeri en düşük bölüm sonucudur.
- Bir katalog kablosunun tek-kablo referans akımı `N` paralel kablo için yalnız `Iref × N` aritmetik toplamı oluşturur. Bu değer proje ampacity'si değildir. Referans kablo/faz sayısı ile hedef kablo/faz sayısı farklıysa explicit `grouping_parallel` düzeltme faktörü gerekir.
- IEC 60287 steady-state kapsamı `%100 load factor` ve sürekli sabit akımdır. Katalog reference `load_factor != 1.0` ise rating, IEC 60287 skaler düzeltme zincirine sokulmaz; `CYCLIC_REFERENCE_REQUIRES_IEC60853` olarak ayrılır.
- Aynı projeye uygulanmış aynı katalog snapshot'ı ve aynı paralel sayısı için fiziksel proje ampacity'si mevcutsa normalize katalog benchmark'ı ile yönlü fark raporlanır. Bu fark için bu sürümde keyfi bir kabul yüzdesi uygulanmaz; nihai uygunluk FAZ 4.2 yöntem otoritesi altındaki IEC/nodal fiziksel proje sonucudur.
- İlk tasarım jenerik aday motorundaki açıklamasız `0.90` paralel derating kaldırılmıştır. Çoklu kablo/faz tahmini yalnız aritmetik L1 ön-eleme üst sınırıdır ve `GRUPLAMA_DOGRULAMASI_GEREKLI` olarak işaretlenir.
