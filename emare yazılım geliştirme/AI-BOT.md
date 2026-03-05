# 🤖 AI-BOT — Yazılım Geliştirme Önerileri

> **Proje:** Emarebot — E-Ticaret Otomasyon Botu  
> **Uzmanlık:** Python + Trendyol/Hepsiburada API + Web Scraping + Selenium  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — E-Ticaret Entegrasyon Katmanı (Ortak)

**Öncelik:** 🔴 Kritik  
**Kapsam:** Emarebot, Emare Finance, Emare POS

### Sorun
Trendyol, Hepsiburada, N11 API'leri farklı davranıyor. Her proje kendi entegrasyonunu yazarsa kod duplicasyonu kaçınılmaz.

### Öneri
**Emare Marketplace Connector** servisi: tüm platformları tek API altında topla.

```python
# Tek API, tüm platformlar
connector = MarketplaceConnector("trendyol")
orders = connector.get_orders(since="2026-03-01")
connector.update_stock(product_id=123, quantity=50)
connector.get_products(page=1, limit=100)
```

### Geliştirme Adımları
1. [ ] Trendyol adapter (bizde çalışıyor, refactor et)
2. [ ] Hepsiburada adapter
3. [ ] N11 adapter
4. [ ] Ortak order model (platform bağımsız)
5. [ ] Webhook receiver (platform sipariş bildirimleri)
6. [ ] Emare Finance ile stok sync

### Beklenen Sonuç
E-ticaret entegrasyonu: 1 kod → tüm platformlar

---

## [4 Mart 2026] — Fiyat İzleme & Rakip Analizi Modülü

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emarebot, Emare Finance, Emare Makale

### Sorun
Rakip fiyatları manuel takip ediliyor. Fiyat değişikliklerinde geç kalınıyor.

### Öneri
Otomatik rakip fiyat izleme + AI önerisi sistemi.

### Geliştirme Adımları
1. [ ] Ürün URL havuzu oluştur
2. [ ] Scheduler: saatlik/günlük fiyat scrape
3. [ ] Fiyat history DB (TimeSeries)
4. [ ] AI öneri: "Rakipler X'ten ucuza satıyor, fiyatınızı düşürün" 
5. [ ] Bildirim: WhatsApp/SMS ile fiyat uyarısı
6. [ ] Emare Makale: rakip analiz makaleleri için veri sağla

### Beklenen Sonuç
%20 daha rekabetçi fiyatlama, manuel takip sıfır
