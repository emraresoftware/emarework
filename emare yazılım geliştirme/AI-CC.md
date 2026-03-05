# 🤖 AI-CC — Yazılım Geliştirme Önerileri

> **Proje:** Emare CC — Customer Communications Platform  
> **Uzmanlık:** Çok Kanallı İletişim + CRM + Müşteri Yolculuğu  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Customer 360° Profili

**Öncelik:** 🔴 Kritik  
**Kapsam:** Emare CC, Emare Finance, Emarebot, Emare Asistan

### Sorun
Aynı müşteri Emare Finance'te fatura alıyor, Emarebot'ta sipariş veriyor, Emare Asistan'a soru soruyor. Ama hiçbir proje birbirinin müşteri bilgisini görmüyor. Her proje lokal kayıt tutuyor.

### Öneri
**Emare CC'yi Müşteri Veri Merkezi** yap. Tüm projeler müşteri bilgisini buradan çeker/yazar.

```python
# Müşteri profili API
GET /api/customer/{phone}/profile
→ {
  "name": "Ahmet Yılmaz",
  "phone": "+905551234567",
  "finance": {"invoices": 12, "total_paid": 45000},
  "orders": {"trendyol": 8, "hepsiburada": 3, "total": 11},
  "support": {"tickets": 2, "last_contact": "2026-02-15"},
  "segment": "VIP",
  "lifetime_value": 67500
}
```

### Geliştirme Adımları
1. [ ] Merkezi müşteri modeli (master record)
2. [ ] Emare Finance webhook → CC güncelle
3. [ ] Emarebot webhook → CC güncelle
4. [ ] Emare Asistan: soru sorunca CC'den context al
5. [ ] KVKK: onay yönetimi, veri silme

### Beklenen Sonuç
Müşteri tek profil, tüm projeler koordineli iletişim, %30 daha iyi müşteri deneyimi

---

## [4 Mart 2026] — Omnichannel Mesajlaşma Standardı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare CC, Emare Asistan, Emare Ulak

### Sorun
Müşteri WhatsApp'tan yazıyor, Emare Asistan cevap veriyor. Aynı kişi e-posta gönderiyor, farklı sistem. Telegram'dan giriyor, başka sistem. Konuşma geçmişi dağınık.

### Öneri
Emare CC'de tüm kanallar tek thread: WhatsApp + e-posta + SMS + web chat bir arada.

### Unified Inbox
```
Müşteri: Ahmet Yılmaz
Timeline:
  📱 WhatsApp (10:03): "Faturamı ne zaman alacağım?"
  ✉️  E-posta (10:15): "Sipariş durumumu öğrenebilir miyim?"
  💬 Web Chat (11:30): "Ürün iade etmek istiyorum"
  → Tek ekranda, tek thread
```

### Geliştirme Adımları
1. [ ] Channel adapter: her kanal için adapter
2. [ ] Unified customer thread DB
3. [ ] Agent UI: tek ekranda tüm kanallar
4. [ ] Emare Asistan: AI otomatik cevap (düşük öncelikli)
5. [ ] Escalation: AI yetersizse insan devreye girer

### Beklenen Sonuç
Müşteri nerede yazarsa yazsın tek koordineli cevap, %25 daha hızlı çözüm süresi
