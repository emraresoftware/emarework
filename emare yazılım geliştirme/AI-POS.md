# 🤖 AI-POS — Yazılım Geliştirme Önerileri

> **Proje:** Emare POS / Adisyon — Restoran POS Sistemi  
> **Uzmanlık:** Laravel 12 + SQLite + Alpine.js + Offline-first  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Offline-First Mimari Standart Olmalı

**Öncelik:** 🔴 Kritik  
**Kapsam:** Emare POS, EmareDesk, Emare Ulak

### Sorun
İnternet kesintisinde uygulama durduğunda iş kayıpları oluyor. POS sistemin kesinlikle offline çalışması şart.

### Öneri
**IndexedDB (browser) + SQLite (server)** kombinasyonu: internet yokken lokal çalış, gelince sync et.

### Uygulama
```javascript
// Service Worker ile offline destek
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(cached => cached || fetch(event.request))
  );
});

// Sync queue - internet gelince at
const queue = new BackgroundSyncQueue('emare-pos-sync');
await queue.pushRequest({ request: paymentRequest });
```

### Geliştirme Adımları
1. [ ] Service Worker kurulumu (tüm statik varlıklar)
2. [ ] IndexedDB ile lokal sipariş kaydı
3. [ ] SQLite sync protokolü (conflict resolution)
4. [ ] "Offline mod" indikatörü (kırmızı banner)
5. [ ] Test: 1 saatlik offline simülasyonu

### Beklenen Sonuç
İnternet kesintisi = sıfır iş kaybı

---

## [4 Mart 2026] — Garson App'i (PWA)

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare POS, Emare Team

### Sorun
Garsonlar masaüstü POS'a bağımlı. Tablet/telefon ile sipariş alınamıyor.

### Öneri
Mevcut POS'u **PWA** olarak paketle. Garson telefona yükler, masada sipariş alır.

### Geliştirme Adımları
1. [ ] `manifest.json` ekle
2. [ ] Service Worker ile offline destek
3. [ ] Touch-friendly UI (büyük butonlar)
4. [ ] QR kod ile masadan sipariş (müşteri kendi siparişini verir)
5. [ ] Mutfak ekranına anlık bildirim

### Beklenen Sonuç
Garson tableti = %30 daha hızlı servis, %15 daha az hata
