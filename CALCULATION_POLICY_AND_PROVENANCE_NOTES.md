# Hesap Politikası ve Parametre Kökeni — v0.16.3.1

## Amaç

v0.16.3.1, çalışan v0.16.3 hesap motorlarının üzerine eklenen izlenebilirlik katmanıdır. Hiçbir mühendislik değerini kendiliğinden değiştirmez. Aynı skaler alanlar mevcut solverlara gitmeye devam eder; yeni katman bu değerin nasıl elde edildiğini kaydeder.

## Yöntem sınıfları

- `PHYSICAL_AUTO`: standart/denklem/matris motorundan hesaplanan değer
- `CERTIFIED_INPUT`: üretici, test, saha ölçümü veya doğrulanmış as-built girdi
- `MANUAL_OVERRIDE`: otomatik veya sertifikalı değer üzerine gerekçeli kullanıcı kararı
- `LEGACY_COEFFICIENT`: eski/jenerik sabit veya kaynaksız ön tasarım katsayısı

## Statüler

- `CALCULATED`
- `VERIFIED`
- `PRELIMINARY_ONLY`
- `REQUIRES_CONFIRMATION`

## İzlenen ilk parametre grubu

- İletken kesiti, Rdc20 ve α20
- Skin factor `ys` ve proximity factor `yp`
- Kapasitans ve tanδ
- Metalik kılıf kesiti ve Rdc20
- Kılıf kayıp oranı `λ1`
- Zırh kayıp oranı `λ2`
- T1, T2 ve T3
- Zemin ısıl özdirenci
- Gömülme derinliği, faz ve devre aralıkları

## Başlangıç sınıflandırması

v0.16.3'te bulunan `ys`, `yp`, `λ1` ve `λ2` skalerleri otomatik olarak:

- `LEGACY_COEFFICIENT`
- `PRELIMINARY_ONLY`

olarak kaydedilir. Sayısal değerleri değiştirilmez.

Rdc veya kılıf direnci sıfır bırakılmış ve mevcut motor malzeme/kesitten türetiyorsa kayıt `PHYSICAL_AUTO / CALCULATED` olur. Üretici snapshot'ı ve doğrulanmış kaynak bulunduğunda uygun alanlar `CERTIFIED_INPUT` olarak işaretlenebilir.

## λ1 özel davranışı

Bonding/CIM motoru çalıştırılıp `auto_apply_lambda1` etkin olduğunda:

1. Mevcut motor λ1 değerini aynı şekilde hesaplar.
2. Aynı skaler alan `cable.sheath_loss_factor` içine yazılır.
3. Ek olarak kaynak kaydı:
   - `PHYSICAL_AUTO`
   - `CALCULATED`
   - `IEC 60287-1-3; IEEE 575; CIGRE TB 797`
   olarak güncellenir.

λ1 tanımı:

`λ1 = toplam metalik kılıf I²R kaybı / toplam iletken I²R kaybı`

## Değer değişikliği denetimi

Kaynak kaydı oluşturulduğu andaki değer `value_snapshot` olarak tutulur. Bir değer başka ekrandan değiştirilir fakat kaynak/yöntem kaydı yenilenmezse:

`VALUE_CHANGED_WITHOUT_PROVENANCE`

uyarısı üretilir.

## Nihai tasarım politikası

`block_final_with_legacy_coefficients = true` varsayılandır. Etkin legacy katsayılar kaynak denetiminde hata olarak görünür ve denetim sonucu “Nihai tasarım kapısı: BLOKE” olur. Bu sürüm mevcut hesap butonlarını engellemez; ön tasarım hesapları çalışmaya devam eder. Fiziksel motorlar devreye alındıkça ilgili kayıtlar `PHYSICAL_AUTO` durumuna taşınacaktır.

## Arayüz

`Proje → Hesap Parametreleri ve Kaynakları…`

Ekranda mühendislik değeri salt okunurdur. Kullanıcı yalnız:

- yöntem,
- statü,
- kaynak tipi,
- doküman ve sayfa,
- standart,
- geçerlilik kapsamı,
- override gerekçesi/not

alanlarını düzenler. `MANUAL_OVERRIDE` için gerekçe zorunludur.

## Sonraki sürüm

v0.16.4 kablo fiziksel parametre motorudur. İlk hedef, desteklenen iletken konstrüksiyonları için Rdc/Rac, skin, proximity, kapasitans kontrolü, dielektrik kayıp, kılıf direnci ve T1–T3 değerlerini fiziksel olarak üretmek ve bu kayıtları `PHYSICAL_AUTO` statüsüne taşımaktır.
