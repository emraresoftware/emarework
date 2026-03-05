# 🤖 AI-ULAK — Yazılım Geliştirme Önerileri

> **Proje:** Emare Ulak — Real-time Mesajlaşma & Bildirim  
> **Uzmanlık:** WebSocket + SocketIO + Redis Pub/Sub + Push Notifications  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Projeler Arası Real-time Event Bus

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
21 proje birbirine HTTP polling ile iletişim kuruyor. "Yeni sipariş var mı?" için her 5 saniyede istek atılıyor. Bu hem gecikme hem de gereksiz yük.

### Öneri
Emare Ulak'ı **Merkezi Event Bus** yap. Projeler event'leri WebSocket ile anlık alır.

```javascript
// Emare Finance → Ulak'a event yayınla
ulak.publish('emare:invoice:created', {
  invoice_id: 12345,
  customer: 'Ahmet Yılmaz',
  amount: 5000
});

// Emare Asistan → Ulak'a abone ol
ulak.subscribe('emare:invoice:created', (event) => {
  sendWhatsApp(event.customer, `Faturanız oluşturuldu: ${event.amount} TL`);
});
```

### Geliştirme Adımları
1. [ ] Redis Pub/Sub üzerine WebSocket gateway
2. [ ] Topic sistemi: `emare:{project}:{event_type}`
3. [ ] Auth: JWT ile proje bazlı yetkilendirme
4. [ ] Replay: son X event'i kaçıranlar için
5. [ ] Monitoring: hangi event kaç kez, hangi latency

### Beklenen Sonuç
Anlık cross-project haberleşme, polling sıfır, %80 daha az sunucu yükü

---

## [4 Mart 2026] — Push Notification Gateway

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare POS, Emare Finance, Emarebot

### Sorun
Web uygulamalarına bildirim gönderilemiyor. Kullanıcı uygulamayı açık tutmazsa bildirimleri kaçırıyor.

### Öneri
Web Push Notifications + PWA Service Worker ile arka plan bildirimleri.

```javascript
// Kullanıcı abone olur
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: VAPID_PUBLIC_KEY
});

// Sunucu bildirim gönderir (Emare Ulak)
await webpush.sendNotification(subscription, JSON.stringify({
  title: '🍕 Yeni Sipariş!',
  body: 'Masa 7 yemek sipariş etti',
  icon: '/icon.png'
}));
```

### Geliştirme Adımları
1. [ ] VAPID key pair oluştur
2. [ ] Service Worker: push event listener
3. [ ] Subscription DB: kullanıcı → subscription endpoint
4. [ ] API: `POST /api/push/send`
5. [ ] Emare POS: garson telefona bildirim

### Beklenen Sonuç
Mobil uygulama olmadan native bildirim, kullanıcı her zaman haberdar
