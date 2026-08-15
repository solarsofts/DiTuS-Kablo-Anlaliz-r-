# DiTuS Raporlama Motoru — Tasarım ve İzlenebilirlik Notları

## 1. Amaç

Raporlama katmanı hesap motorlarının yerine geçmez ve sonuç üretmez. Proje modelindeki girdileri, kaynak kayıtlarını ve kullanıcı oturumunda gerçekten hesaplanmış sonuçları tek bir değişmez rapor modelinde toplar.

Temel kural:

```text
Proje girdileri + mevcut hesap sonuçları
→ seçilmiş rapor modülleri
→ zorunlu uyarı/sınırlama kapısı
→ tek rapor modeli
→ DOCX / PDF / HTML / Markdown / JSON
```

## 2. Rapor şablonları

Şablonlar yalnız başlangıç modül seçimini belirler. Kullanıcı tek ekrandan bölüm ekleyip çıkarabilir. Kritik güvenlik ve veri yeterliliği uyarıları hiçbir şablonda kapatılamaz.

- **Hesap Raporu:** hesap girdisi, sonuç, yöntem ve hesap izi ağırlıklıdır.
- **Proje/Tasarım Raporu:** seçilen tasarım, güzergâh, kablo ve karar özeti ağırlıklıdır.
- **Kısa Teknik Özet:** yönetici/inceleme seviyesi kısa çıktı verir.
- **Tam Tasarım Dosyası:** mevcut bütün hesap ve proje modüllerini içerir.

## 3. Sonuç durumu

Bir modül için üç temel durum ayırt edilir:

- `AVAILABLE`: sonuç çalışma belleğinde vardır ve rapora alınmıştır.
- `NOT_RUN`: modül seçilmiştir fakat hesap sonucu yoktur.
- `ATTENTION`: kaynak çelişkisi, koşullu veri veya açık iş vardır.

Rapor üretmek bir tasarım onayı değildir. `CONDITIONAL`, `NOT_READY`, `NOT_RUN` ve benzeri durumlar metin içinde ve zorunlu uyarılar bölümünde görünür tutulur.

## 4. Kaynak ve hesap izi

Her rapor:

- proje kodu ve doküman kimliği,
- proje JSON içeriğinden üretilen SHA-256 imzası,
- veri kaynağı ve doğrulama durumu,
- kaynak çelişkileri ve eksik bilgiler,
- kullanılan hesap sonuçlarının kompakt veya ayrıntılı izi

ile yeniden izlenebilir.

Kompakt hesap izi varsayılandır. Ayrıntılı iz kullanıcı tarafından açılır; büyük raporlarda ham solver satırlarının belgeyi gereksiz büyütmesi önlenir.

## 5. Çıktı üretimi

- **JSON:** makinece okunabilir tam rapor modeli.
- **Markdown:** hızlı inceleme, sürüm kontrolü ve metin tabanlı arşiv.
- **HTML:** bağımsız, yazdırılabilir ve internet gerektirmeyen çıktı.
- **DOCX:** kurumsal düzenleme ve kontrollü doküman süreci.
- **PDF:** değişmez paylaşım ve teknik teslim çıktısı.

DOCX ve PDF aynı içerik modelinden üretilir. Geniş SVL tablolarında bekleyen/başarısız kontroller ayrı not satırlarına taşınarak sayfa okunabilirliği korunur.

## 6. Proje nesnesini değiştirmeme ilkesi

Rapor oluşturma sırasında gerilim düşümü ve iterasyon kapısı gibi yardımcı değerlendirmeler proje kopyası üzerinde çalışır. Rapor üretimi:

- kablo snapshot'ını,
- güzergâh atamalarını,
- kullanıcı kararlarını,
- sonuç nesnelerini

değiştiremez.

Bu davranış otomatik regresyon testiyle korunur.

## 7. v0.16.1 tedarik bağlantısı

BOQ/BOM/RFQ raporun içine elle yazılan tablolar değildir. v0.16.1 tedarik kalemi modeli; kablo, termination, joint, link box, SVL, bonding iletkeni, ECC/GCC, topraklama ve isteğe bağlı inşaat nesnelerinden otomatik türetilir. Raporlama motoru bu kalemleri seçilebilir **BOQ/BOM ve tedarik özeti** bölümü olarak kullanır; ayrıntılı XLSX/CSV/RFQ ve makara planı ayrı tedarik paketinden üretilir.

## 8. Kontrast ve görsel çıktı kuralı

Koyu lacivert bölüm bantları ve tablo başlıklarında yazı rengi beyazdır. Bu kural DOCX, PDF, HTML ve XLSX çıktılarında ortaktır. ReportLab tablolarında yalnız `TEXTCOLOR` komutuna güvenilmez; başlık hücrelerindeki `ParagraphStyle` da beyaz metinle oluşturulur. Örnek DOCX/PDF raporlar render edilerek görsel regresyon kontrolünden geçirilir.
