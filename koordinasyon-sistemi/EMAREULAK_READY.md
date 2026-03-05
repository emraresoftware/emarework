# 🚀 EmareUlak 100 Proje Test - Hızlı Başlangıç

## ✅ Hazırlıklar Tamamlandı! (4 Mart 2026)

### Oluşturulan Dosyalar:

1. **Test Konfigürasyonu**: [config/test_100_projects.yml](config/test_100_projects.yml)
2. **EmareUlak Köprüsü**: [src/emareulak_bridge.py](src/emareulak_bridge.py)
3. **API Endpoint'leri**: [src/api/main.py](src/api/main.py) (EmareUlak bölümü eklendi)
4. **Test Script**: [test_100_projects.py](test_100_projects.py)
5. **API Başlatma**: [start_api.sh](start_api.sh)

---

## 📊 Test Sonuçları

**İlk Test Çalıştırması (4 Mart 2026 01:32:59):**

```
✓ 111 düğüm kaydedildi (L0 → L1(10) → L2(100))
✓ 100 proje dağıtıldı
✓ Süre: 0.30 saniye
✓ Ortalama: 3.0ms/proje
✓ Başarı oranı: 100%
✓ Hatalı: 0
```

**Performans:**
- Paralel dağıtım: 10'lu gruplar
- Strateji: weighted (yük bazlı)
- Otomatik yük dengeleme: Aktif

---

## 🎯 Kullanım Komutları

### 1. API Sunucusunu Başlat

```bash
cd "/Users/emre/Desktop/Emare/yazılım ekibi/koordinasyon-sistemi"

# Manuel başlatma
python3 -B -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

# Ya da script ile
./start_api.sh
```

**API Erişim:**
- Ana sayfa: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Hierarchy: http://127.0.0.1:8000/hierarchy

### 2. Test Senaryosunu Çalıştır

```bash
cd "/Users/emre/Desktop/Emare/yazılım ekibi/koordinasyon-sistemi"

# Varsayılan (100 proje, weighted)
python3 -B test_100_projects.py

# Farklı seçenekler
python3 -B test_100_projects.py --projects 50           # 50 proje
python3 -B test_100_projects.py --strategy cascade      # Cascade stratejisi
python3 -B test_100_projects.py --strategy round-robin  # Round-robin
python3 -B test_100_projects.py --sequential            # Sıralı dağıtım

# Tam kontrol
python3 -B test_100_projects.py \
  --projects 100 \
  --strategy weighted \
  --api http://localhost:8000
```

---

## 🔌 EmareUlak API Endpoint'leri

### Tek Proje Dağıt
```bash
curl -X POST http://127.0.0.1:8000/emareulak/project \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "ULAK-001",
    "title": "Test Projesi",
    "description": "Test açıklaması",
    "priority": "high",
    "estimated_kb": 30720,
    "tags": ["test"]
  }'
```

### Toplu Proje Dağıt
```bash
curl -X POST http://127.0.0.1:8000/emareulak/batch \
  -H "Content-Type: application/json" \
  -d '{
    "projects": [...],
    "parallel": true,
    "strategy": "weighted"
  }'
```

### Proje Durumu Sorgula
```bash
# Tek proje
curl http://127.0.0.1:8000/emareulak/status/ULAK-001

# Tüm projeler
curl http://127.0.0.1:8000/emareulak/status

# İstatistikler
curl http://127.0.0.1:8000/emareulak/stats
```

### Proje İptal Et
```bash
curl -X DELETE http://127.0.0.1:8000/emareulak/project/ULAK-001
```

---

## ⚙️ Dağıtım Stratejileri

| Strateji | Açıklama | Kullanım |
|----------|----------|----------|
| **weighted** | Yük bazlı (düşük yüklü düğüme daha fazla) | Varsayılan, dengeli |
| **cascade** | Kademeli bölme (10'a böl) | Büyük görevler |
| **round-robin** | Sırayla dağıt | Eşit görevler |
| **least-loaded** | En boş düğüme | Hızlı dağıtım |

---

## 📈 Hiyerarşi Yapısı

```
L0 (1)      → Genel Koordinatör
└── L1 (10)   → Takım Liderleri
    └── L2 (100) → Projeler/Geliştiriciler

Toplam: 111 düğüm
```

---

## 🔧 Yaplandırma

Test ayarlarını değiştirmek için: [config/test_100_projects.yml](config/test_100_projects.yml)

```yaml
test_scenario:
  total_projects: 100
  hierarchy:
    depth: 2
    
emareulak:
  enabled: true
  distribution_strategy: "weighted"
  auto_assign: true
  load_balancing: true
  
performance:
  batch_register_size: 100
  aggregation_interval_sec: 10
  max_concurrent_projects: 100
```

---

## 📝 Sonraki Adımlar

1. **Gerçek EmareUlak entegrasyonu**: Webhook/API bağlantısı ekle
2. **WebSocket desteği**: Gerçek zamanlı durum güncellemeleri
3. **Dashboard**: React/Vue frontend ekle
4. **PostgreSQL**: Kalıcı veri saklama (şu an bellek içi)
5. **Monitoring**: Grafana dashboard'ları

---

## 🐛 Sorun Giderme

**API başlamıyor:**
```bash
# Port kontrolü
lsof -i :8000

# Loglara bak
tail -f logs/hive_coordinator.log
```

**Test bağlanamıyor:**
```bash
# API durumunu kontrol et
curl http://127.0.0.1:8000/

# Firewall kontrolü
sudo lsof -i :8000
```

---

## 📞 İletişim

**API Dokümantasyonu:** http://127.0.0.1:8000/docs  
**Ana Döküman:** [hafıza.md](../hafıza.md)  
**Tasarım Rehberi:** [DESIGN_GUIDE.md](../DESIGN_GUIDE.md)

---

**Test hazır! EmareUlak görevleri dağıtmaya başlayabilir. 🚀**
