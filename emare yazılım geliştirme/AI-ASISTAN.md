# 🤖 AI-ASISTAN — Yazılım Geliştirme Önerileri

> **Proje:** Emare Asistan — Multi-tenant SaaS AI Platform  
> **Uzmanlık:** FastAPI + Gemini AI + WhatsApp Bridge + Celery  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Ekosistem Genelinde AI Tabanlı Bildirim Altyapısı

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
Her proje kendi bildirim sistemini kurmuş (bazıları SMS, bazıları e-posta, bazıları hiçbiri). Kullanıcılar farklı kanallardan mesaj alıyor, tutarlılık yok.

### Öneri
Benim WhatsApp + SMS altyapımı tüm ekosisteme açık bir **Merkezi Bildirim Servisi** olarak sun. Tüm projeler `POST /api/notify` ile bildirim göndersin.

### Geliştirme Adımları
1. [ ] `/api/notify` endpoint'i stabilize et (tüm projelere açık)
2. [ ] Kanal seçimi: `WhatsApp`, `SMS`, `E-posta`, `Push`
3. [ ] Rate limiting: Her proje için kota tanımla
4. [ ] Webhook ile geri bildirim (mesaj iletildi mi/okundu mu)
5. [ ] Emare Finance → fatura bildirimi
6. [ ] Emare Log → alarm bildirimi
7. [ ] Hive Coordinator → görev bildirimi

### Beklenen Sonuç
21 projenin tamamı tek API ile bildirim gönderir, `%80 daha az tekrar kod`

---

## [4 Mart 2026] — Gemini Context Cache Zorunlu Kılınmalı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** EmareSetup, AI-AI, EmareHup

### Sorun
Gemini API maliyetleri yüksek çünkü her istekte context yeniden gönderiliyor.

### Öneri
Gemini 1.5'in **Context Caching** özelliğini kullanın. Sistem prompt'unu bir kez cache'leyin.

### Kod Örneği
```python
from google import genai

client = genai.Client()

# System context'i bir kez cache'le
cache = client.caches.create(
    model="gemini-1.5-flash-001",
    contents=[{"parts": [{"text": system_context}]}],
    ttl=3600  # 1 saat
)

# Her istekte cache ID'yi kullan
response = client.models.generate_content(
    model="gemini-1.5-flash-001",
    cached_content=cache.name,
    contents=user_message
)
```

### Beklenen Sonuç
`%70 maliyet düşüşü` (kendi deneyimimizden)

---

## [4 Mart 2026] — Multi-Agent Sistemleri İçin Celery Standardı

**Öncelik:** 🟡 Orta  
**Kapsam:** EmareHup, EmareSetup, Hive Coordinator

### Sorun
Her proje farklı task queue sistemi kullanıyor veya hiç kullanmıyor (blocking calls).

### Öneri
Redis + Celery standardı tüm ekosistemde olmalı.

### Geliştirme Adımları
1. [ ] Ortak Celery config template (EMARE_ORTAK_CALISMA'ya ekle)
2. [ ] Redis tek instance (5555 portunda Hub gibi)
3. [ ] Task priority sistemi: `high`, `normal`, `low`
4. [ ] Flower dashboard ile tüm taskları izle

### Beklenen Sonuç
Asenkron görevler güvenilir, izlenebilir, ölçeklenebilir olur
