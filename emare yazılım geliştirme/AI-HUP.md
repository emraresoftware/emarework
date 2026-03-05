# 🤖 AI-HUP — Yazılım Geliştirme Önerileri

> **Proje:** EmareHup — DevM Multi-Agent Geliştirme Ortamı  
> **Uzmanlık:** Node.js + Python Bridge + Agent Orkestrasyonu + LLM  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — DevM Agent'ları Tüm Projelere Açılmalı

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
DevM agent'ları sadece EmareHup içinde çalışıyor. Diğer projeler de AI code assistant'tan yararlanabilir.

### Öneri
DevM'i **API gateway** haline getir. Herhangi bir proje `POST /devm/task` ile agent'a iş verebilsin.

```json
POST /api/devm/task
{
  "project": "emare-finance",
  "task": "Add pagination to /api/invoices endpoint",
  "context_files": ["app/Http/Controllers/InvoiceController.php"],
  "output": "diff"
}
```

### Geliştirme Adımları
1. [ ] DevM REST API stabilize et
2. [ ] Multi-project context: agent proje kodunu okuyabilsin
3. [ ] Output format: `diff`, `pr`, `comment`, `file`
4. [ ] Task queue (Celery): agent'lar arka planda çalışsın
5. [ ] Sonuç hook: tamamlanınca bildirim gönder

### Beklenen Sonuç
21 proje AI destekli geliştirme yapabilir, %40 daha hızlı sprint

---

## [4 Mart 2026] — Agent Hiyerarşisi: Hive Coordinator Entegrasyonu

**Öncelik:** 🟠 Yüksek  
**Kapsam:** EmareHup, Hive Coordinator

### Sorun
DevM agent'ları düz (flat) çalışıyor. 10 milyarlık hiyerarşik sistemden yararlanılmıyor.

### Öneri
Hive Coordinator'ın **ağaç yapısını** kullanarak agent'ları hiyerarşik organize et.

```
Root Agent (Koordinatör)
├── Backend Agent (FastAPI görevleri)
│   ├── Database Agent (migration, model)
│   ├── API Agent (endpoint, validation)
│   └── Test Agent (pytest, coverage)
├── Frontend Agent (React/HTML görevleri)
└── DevOps Agent (Docker, deploy)
```

### Geliştirme Adımları
1. [ ] Hive Coordinator API ile bağlantı
2. [ ] Agent tipi → Hive node mapping
3. [ ] Görev dağıtımı: root agent büyük görevi alt agent'lara böler
4. [ ] Paralel execution: bağımsız alt görevler aynı anda çalışır
5. [ ] Sonuç toplama: alt agent'ların çıktısı merge edilir

### Beklenen Sonuç
Büyük görevler paralel çözülür, 5x hızlanma
