# 🤖 AI-ADS — Yazılım Geliştirme Önerileri

> **Proje:** Emare Ads — Reklam Yönetim Platformu  
> **Uzmanlık:** Meta/Google Ads API + Kampanya Optimizasyonu + Analytics  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Ürünleri İçin Reklam Otomasyonu

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare Ads, Emare Makale, Emarebot

### Sorun
Emare ürünleri büyüyor ama reklam yok. Her proje kendi lansmanını kendi yapıyor (veya yapmıyor).

### Öneri
Yeni özellik/proje lansmanında **otomatik reklam kampanyası** başlat.

### Otomatik Kampanya Akışı
```
1. Yeni proje/özellik → Emare Makale'den içerik al
2. Emare Ads → Hedef kitle belirle (B2B/B2C)
3. Reklam görseli: EMARE_ORTAK_TASARIM.md tasarım sistemiyle üret
4. Meta + Google'a kampanya gönder
5. A/B test: 2 farklı kreatif
6. 3 gün sonra: performans analizi + oto-optimizasyon
```

### Geliştirme Adımları
1. [ ] Meta Business API entegrasyonu
2. [ ] Google Ads API entegrasyonu
3. [ ] Kreatif üretici: Gemini + tasarım sistemi
4. [ ] A/B test framework
5. [ ] ROI dashboard: hangi kampanya ne getirdi

### Beklenen Sonuç
Lansman = anlık reklam kampanyası, sıfır manuel iş

---

## [4 Mart 2026] — First-Party Data Stratejisi

**Öncelik:** 🟡 Orta  
**Kapsam:** Emare Ads, Emare Finance, Emarebot

### Sorun
3rd party cookie'ler bitiyor. Hedefleme giderek zorlaşıyor. Emare'nin kendi müşteri datasına ihtiyacı var.

### Öneri
Emare Finance ve Emarebot müşteri verisini (KVKK uyumlu) Emare Ads'e aktar.

### Geliştirme Adımları
1. [ ] Customer Data Platform (CDP) tasarımı
2. [ ] Emare Finance → müşteri profili (KVKK onaylı)
3. [ ] Emarebot → alışveriş davranışı
4. [ ] KVKK: açık rıza yönetimi
5. [ ] Meta/Google Custom Audiences ile yükle

### Beklenen Sonuç
%40 daha iyi reklam hedefleme, 3rd party cookie bağımlılığı sıfır
