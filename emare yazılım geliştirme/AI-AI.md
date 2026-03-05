# 🤖 AI-AI — Yazılım Geliştirme Önerileri

> **Proje:** Emare AI — AI Model Yönetim & Inference Platformu  
> **Uzmanlık:** LLM Orchestration + Model Registry + Prompt Engineering + RAG  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Merkezi AI Gateway (Tüm Projeler İçin)

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm AI kullanan projeler

### Sorun
Emare Asistan Gemini, EmareSetup Gemini, EmareHup farklı model, Emare Katip başka model kullanıyor. Her proje API key'ini ayrı manage ediyor. Maliyet kontrolü yok, rate limit yönetimi yok.

### Öneri
**Emare AI Gateway**: tüm LLM çağrıları tek noktadan geçer.

```python
# Tüm projeler bu gateway'i kullanır
import emare_ai

response = emare_ai.generate(
    project="emare-finance",
    prompt="Bu faturayı özetle: ...",
    model="gemini-1.5-flash",  # veya "gpt-4o", "claude-3"
    priority="normal"
)
```

### Gateway Özellikleri
- **Model Router:** En ucuz/hızlı modeli seç
- **Cache:** Aynı prompt tekrar gelirse cache'den dön
- **Rate Limiter:** Proje bazlı kota
- **Cost Tracker:** Hangi proje ne kadar harcadı
- **Fallback:** Model down → otomatik alternatife geç

### Geliştirme Adımları
1. [ ] API Gateway servisi (FastAPI)
2. [ ] Model adapter: Gemini, GPT-4o, Claude
3. [ ] Semantic cache (aynı anlam = aynı cache)
4. [ ] Cost dashboard: proje bazlı harcama
5. [ ] Circuit breaker: model rate limit yiyor → fallback

### Beklenen Sonuç
%60 AI maliyeti azalması, sıfır API key yönetimi sorunu

---

## [4 Mart 2026] — RAG Sistemi: Emare Bilgi Tabanı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare AI, Emare Asistan, Emare Katip

### Sorun
AI'lar Emare projelerini, süreçlerini, müşteri verilerini bilmiyor. Sorulara genel cevaplar veriyor.

### Öneri  
Tüm EMARE_ORTAK_CALISMA dokümanlarını vektör DB'ye ekle. AI'lar sorularda bu bilgiyi kullansın.

```python
# Vektör DB'ye yükle
vectordb.add_documents([
    EMARE_ORTAK_HAFIZA,
    EMARE_ANAYASA,
    EMARE_AI_COLLECTIVE,
    # + her projenin hafıza dosyası
])

# RAG ile soru cevap
response = rag.query("Emare Finance hangi port'ta çalışıyor?")
# → "8000 port'unda çalışıyor (projects.json'dan)"
```

### Geliştirme Adımları
1. [ ] Chroma/Pinecone vektör DB
2. [ ] Doküman loader: tüm *.md dosyalar
3. [ ] Embedding: Gemini text-embedding-004
4. [ ] RAG chain: soru → retrieve → generate
5. [ ] Günlük güncelleme: yeni .md dosyalar otomatik eklenir

### Beklenen Sonuç
AI'lar Emare hakkında %100 doğru sorular yanıtlar
