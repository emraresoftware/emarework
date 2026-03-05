# 🤖 AI-DESK — Yazılım Geliştirme Önerileri

> **Proje:** EmareDesk — Remote Desktop & Screen Sharing  
> **Uzmanlık:** Python + WebSocket + Screen Capture + mss  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Uzak Ekran İzleme API'si (Tüm Projelere Açık)

**Öncelik:** 🟠 Yüksek  
**Kapsam:** SiberEmare, EmareCloud, EmareHup

### Sorun
Debug yaparken sunucu ekranını görmek istiyoruz. SSH çıktısı yetmiyor, görsel gerekiyor.

### Öneri
EmareDesk'i `REST API + WebSocket` olarak aç. Diğer projeler istediklerinde ekran görüntüsü alabilsin.

### API
```python
# GET /api/screenshot?host=192.168.1.10
# Response: base64 PNG

# WS /stream?host=192.168.1.10
# Stream: binary JPEG frames @ 15FPS
```

### Geliştirme Adımları
1. [ ] REST endpoint: tek screenshot
2. [ ] WebSocket: canlı stream
3. [ ] Auth: JWT token ile erişim kontrolü
4. [ ] Kalite seçimi: `low/medium/high`
5. [ ] EmareCloud dashboard'a entegrasyon: her container'ın ekranı

### Beklenen Sonuç
Görsel debugging, uzak makine kontrolü, güvenlik denetimleri

---

## [4 Mart 2026] — Kayıt Özelliği + Replay

**Öncelik:** 🟡 Orta  
**Kapsam:** SiberEmare, EmareCloud

### Sorun
Güvenlik incelemeleri ve bug reproduksiyon için ekran kayıtları lazım.

### Öneri
Screen session'ları kaydet, MP4 veya frame sequence olarak sakla.

### Geliştirme Adımları
1. [ ] Frame buffer → MP4 (ffmpeg pipeline)
2. [ ] Zaman damgalı kayıt (timestamp overlay)
3. [ ] S3/LXD storage'a yükle
4. [ ] Replay API: belirli zaman dilimini izle
5. [ ] SiberEmare entegrasyonu: pentest oturumu otomatik kayıt

### Beklenen Sonuç
Güvenlik audit trail, bug replay, eğitim materyali
