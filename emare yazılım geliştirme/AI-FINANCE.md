# 🤖 AI-FINANCE — Yazılım Geliştirme Önerileri

> **Proje:** Emare Finance — POS + İşletme Yönetimi  
> **Uzmanlık:** Laravel 12 + PHP 8.4 + e-Fatura + SMS + Multi-tenant  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Ödeme Altyapısı (Ortak)

**Öncelik:** 🔴 Kritik  
**Kapsam:** Emare Finance, Emare POS, Emarebot, Emare Token

### Sorun
Her ödeme alan proje ayrı gateway entegrasyonu yapıyor. İyzico'yu 3 proje ayrı ayrı entegre etmiş/edecek.

### Öneri
Tek bir **Emare Payment Microservice** yaz. Tüm projeler ödeme için bunu kullansın.

### API Tasarımı
```json
POST /api/payment/create
{
  "project": "emare-finance",
  "amount": 1500.00,
  "currency": "TRY",
  "customer": {"name": "Ali Veli", "email": "ali@example.com"},
  "callback_url": "https://finance.emare.com/payment/callback"
}
```

### Geliştirme Adımları
1. [ ] İyzico, Stripe, Papara adaptörü
2. [ ] Webhook sistemi (ödeme sonucu projeye bildir)
3. [ ] Fatura otomatik kesme (e-Fatura entegrasyonu)
4. [ ] Refund yönetimi
5. [ ] Dashboard: tüm projeler için gelir analizi

### Beklenen Sonuç
Tek ödeme kodu, 21 projede kullanılabilir

---

## [4 Mart 2026] — e-Fatura Servis Paylaşımı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare Finance, Emare Log, Emarebot

### Sorun
e-Fatura entegrasyonu karmaşık. Her proje tekrar yapmamalı.

### Öneri
Bizim **çalışan** e-Fatura kodunu API olarak paylaşalım.

```php
// Laravel Route
Route::post('/api/efatura/create', [EFaturaController::class, 'create']);
Route::get('/api/efatura/{uuid}', [EFaturaController::class, 'show']);
```

### Geliştirme Adımları
1. [ ] Mevcut e-Fatura kodunu API endpoint'e dönüştür
2. [ ] API key ile diğer projelere yetkilendirme
3. [ ] Rate limiting (fatura başına ücret)
4. [ ] Test modu (sandbox)

### Beklenen Sonuç
Tüm ekosistem yasal e-Fatura kullanabilir, sıfır duplikasyon

---

## [4 Mart 2026] — SMS Havuzu Standardizasyonu

**Öncelik:** 🟡 Orta  
**Kapsam:** Tüm bildirim kullanan projeler

### Sorun
Biz Netgsm kullanıyoruz ve çalışıyor. Diğer projeler farklı sağlayıcı deniyor.

### Öneri
Tüm ekosistem için tek Netgsm hesabı, tek API. Emare Asistan'ın bildirim servisiyle entegre.

### Beklenen Sonuç
SMS maliyeti düşer (toplu kullanım indirimi), tek sağlayıcı = tek sorun noktası
