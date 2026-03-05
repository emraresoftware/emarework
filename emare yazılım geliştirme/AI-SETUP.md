# 🤖 AI-SETUP — Yazılım Geliştirme Önerileri

> **Proje:** EmareSetup — AI Yazılım Fabrikası  
> **Uzmanlık:** FastAPI + React 19 + Gemini + Alembic + Otonom Üretim  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Modül Üretimi Tüm Projelere Açılmalı

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
Her proje yeni özellik yazarken sıfırdan başlıyor. CRUD endpoint'ler, model dosyaları, migration'lar tekrar tekrar yazılıyor.

### Öneri
EmareSetup'ın **AI kod üretim motorunu** diğer projelere API olarak aç.

```
POST /api/generate
{
  "project_type": "fastapi",
  "module_name": "invoice",
  "fields": ["id:int", "customer_id:int", "amount:float", "created_at:datetime"],
  "features": ["crud", "pagination", "search", "export_csv"]
}
→ Hazır endpoint, model, migration, test kodu döner
```

### Geliştirme Adımları
1. [ ] `/api/generate` endpoint'i stabilize et
2. [ ] Desteklenen framework'ler: FastAPI, Flask, Laravel, Express
3. [ ] Test kodu da üret (pytest, phpunit)
4. [ ] EmareHup DevM ile entegrasyon (agent kod üretir)
5. [ ] Output: GitHub PR veya doğrudan dosya

### Beklenen Sonuç
%60 daha az boilerplate kod, geliştiriciler iş mantığına odaklanır

---

## [4 Mart 2026] — Proje İskelet Şablonları (Boilerplate)

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Yeni başlayan her Emare projesi

### Sorun
Her yeni proje kurulumu 2-3 gün sürüyor (config, auth, DB, logging, test setup vs).

### Öneri
Onaylı, production-ready **Emare Proje Şablonları** hazırla.

### Şablon Listesi
```
emare-fastapi-template/
├── app/
│   ├── api/          ← Hazır router yapısı
│   ├── models/       ← SQLAlchemy base model
│   ├── services/     ← Service layer pattern
│   └── core/         ← Config, auth, logging
├── tests/            ← pytest + fixtures
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

### Geliştirme Adımları
1. [ ] FastAPI template (Python projeler için)
2. [ ] Laravel template (PHP projeler için)
3. [ ] EmareCloud tasarım sistemi entegreli frontend template
4. [ ] `emare init --type fastapi` CLI komutu
5. [ ] Her şablon: health check, JWT auth, CORS, logging, Sentry hazır

### Beklenen Sonuç
Yeni proje = 30 dakika setup, %0 boilerplate yazma
