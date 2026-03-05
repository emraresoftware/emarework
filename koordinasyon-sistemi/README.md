# 🐝 Hive Coordinator

## 9 Milyar Düğümlü Hiyerarşik Yazılım Ekibi Koordinasyon Sistemi

---

## 📋 Problem

10 kişilik bir yazılım ekibiniz var. Bu 10 kişinin her birinin kendi 10 kişilik grubu var. Ve bu yapı **10 seviye** derinlikte tekrarlanıyor:

```
Seviye 0:  1 kişi           → Siz (Genel Koordinatör)
Seviye 1:  10 kişi          → Bölge Direktörleri
Seviye 2:  100 kişi         → Kıta Yöneticileri
Seviye 3:  1,000 kişi       → Ülke Müdürleri
Seviye 4:  10,000 kişi      → Bölge Müdürleri
Seviye 5:  100,000 kişi     → Şehir Koordinatörleri
Seviye 6:  1,000,000 kişi   → İlçe Liderleri
Seviye 7:  10,000,000 kişi  → Takım Kaptanları
Seviye 8:  100,000,000 kişi → Kıdemli Geliştiriciler
Seviye 9:  1,000,000,000    → Geliştiriciler
Seviye 10: 10,000,000,000   → Uygulayıcılar
─────────────────────────────────────────
TOPLAM:    ~11.1 Milyar düğüm
```

## 🎯 Çözüm

Hive Coordinator, bu devasa hiyerarşiyi **kademeli (cascade)** prensiple yönetir:

> **Her düğüm sadece kendi 10 çocuğunu yönetir.**  
> Yani hiçbir kişi 10'dan fazla kişiyle doğrudan iletişim kurmaz.

### Temel İlkeler

| İlke | Açıklama |
|------|----------|
| **Kademeli Yönetim** | Her düğüm sadece 10 çocuğunu yönetir |
| **O(log₁₀ N) Yayılma** | Bir mesaj 10 adımda 9 milyar kişiye ulaşır |
| **Alttan Üste Toplama** | Veriler yukarı doğru özetlenerek toplanır |
| **Otonom Takımlar** | Alt seviyeler kendi içinde karar verir |
| **Yük Dengeleme** | İş otomatik olarak boş düğümlere aktarılır |

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                        HIVE COORDINATOR                          │
├─────────────┬──────────────┬──────────────┬────────────────────┤
│  REST API   │ Coordination │    Task      │    Message         │
│  (FastAPI)  │    Engine    │ Distributor  │    Cascade         │
├─────────────┼──────────────┼──────────────┼────────────────────┤
│             │              │              │                    │
│  Düğüm      │ Durum Toplama│ Kademeli     │ Emir/Rapor/Yayın  │
│  Yönetimi   │ Yük Dengeleme│ Parçalama    │ Eskalasyon         │
│  Heartbeat  │ Sağlık Kont. │ İlerleme     │ Gelen Kutusu       │
│             │              │              │                    │
├─────────────┴──────────────┴──────────────┴────────────────────┤
│    PostgreSQL (Partitioned)  │  Redis (Cache + Queue)           │
│    Celery (Async Tasks)      │  Structlog (Logging)             │
└─────────────────────────────────────────────────────────────────┘
```

### Bileşenler

#### 1. Koordinasyon Motoru (`coordination_engine.py`)
- Düğüm kaydı ve yaşam döngüsü
- Heartbeat ile sağlık kontrolü
- Alt ağaç istatistik toplama (aggregation)
- Yük dengeleme ve rebalancing
- Optimal yol bulma (görev ataması için)

#### 2. Görev Dağıtıcı (`task_distributor.py`)
- **CASCADE**: Görev aşağı doğru 10'a bölünür
- **WEIGHTED**: Yüke göre orantılı dağıtım
- **BROADCAST**: Tüm alt ağaca aynı görev
- **TARGETED**: Belirli düğüme doğrudan atama
- İlerleme yukarı doğru toplanır
- Alt görevler bitince üst görev otomatik kapanır

#### 3. Mesaj Kaskadı (`message_cascade.py`)
- **DIRECTIVE**: Yukarıdan aşağı emirler
- **REPORT**: Aşağıdan yukarı raporlar
- **BROADCAST**: Tüm alt ağaca yayın
- **ESCALATION**: Sorunları üste iletme
- **PEER**: Aynı seviye iletişim

#### 4. Adres Sistemi (`addressing.py`)
```
Adres: L{seviye}.{indeks0}.{indeks1}...{indeksN}

Örnekler:
  L0           → Kök (Genel Koordinatör)
  L1.3         → 4. Bölge Direktörü
  L3.0.4.7     → Ülke Müdürü (dal0→dal4→dal7)
  L10.0.0.0.0.0.0.0.0.0.0 → En alt yaprak düğüm
```

---

## 🚀 Kurulum ve Kullanım

### Hızlı Başlangıç

```bash
cd koordinasyon-sistemi

# Python bağımlılıkları
pip install -e .

# Simülasyon çalıştır (veritabanı gerektirmez)
python -m src.cli simulate

# Hiyerarşi özeti
python -m src.cli overview

# Ağaç görünümü
python -m src.cli tree 3

# API sunucusu
python -m src.cli serve 8000
```

### Docker ile Tam Kurulum

```bash
# Tüm servisleri başlat
docker-compose up -d

# API Swagger UI
open http://localhost:8000/docs
```

### API Kullanım Örnekleri

```bash
# Sistem durumu
curl http://localhost:8000/

# Hiyerarşi özeti
curl http://localhost:8000/hierarchy

# Düğüm kaydet
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"address": "L1.0", "name": "Avrupa Direktörü"}'

# Toplu düğüm kaydı (3 seviye = 1111 düğüm)
curl -X POST "http://localhost:8000/batch/register-tree?root_address=L0&depth=3"

# Görev oluştur ve dağıt
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Global Platform v2.0",
    "priority": "critical",
    "created_by": "L0",
    "assigned_to": "L0",
    "target_level": 3
  }'

# Emir yayınla (3 seviye aşağı)
curl -X POST "http://localhost:8000/messages/directive?sender=L0&subject=Sprint+Başlangıcı&target_depth=3"

# Alt ağaç analitikleri
curl http://localhost:8000/analytics/subtree/L0

# Sağlık kontrolü
curl http://localhost:8000/analytics/health/L0

# Yük dengeleme
curl -X POST http://localhost:8000/analytics/rebalance/L0
```

---

## 📊 Performans Analizi

### Mesaj Yayılma Karmaşıklığı

| İşlem | Karmaşıklık | 9 Milyar Düğüm İçin |
|-------|-------------|---------------------|
| Yayın (kökten tümüne) | O(N) mesaj, O(log₁₀ N) adım | 10 adım |
| Rapor toplama | O(N) okuma, O(log₁₀ N) adım | 10 adım |
| Düğüm bulma | O(log₁₀ N) | 10 adım |
| Eşler arası mesaj | O(2 × log₁₀ N) | 20 adım |

### Her Düğümün Sorumluluğu

```
Her düğüm EN FAZLA:
├── 10 çocuk yönetir
├── 1 ebeveyne rapor verir
├── 9 kardeşle iletişir
└── Toplam: 20 bağlantı

Hiçbir düğüm 9 milyar düğümü görmez veya yönetmez!
```

### Yük Dengeleme

```
Senaryo: L1.3 aşırı yüklü (%95), L1.7 boş (%15)

Tespit: L0 çocuklarını kontrol eder (10 düğüm)
Karar:  L1.3'ten L1.7'ye yük aktarımı
Etki:   L1.3'ün alt ağacındaki 1.1 Milyar düğüm rahatlar
Süre:   Tek adım (L0 → L1 seviyesi)
```

---

## 🔧 Yapılandırma

`config/settings.yml` dosyasından tüm parametreler ayarlanabilir:

```yaml
hierarchy:
  depth: 10          # Seviye sayısı
  branch_factor: 10  # Her düğümün çocuk sayısı

performance:
  aggregation_interval_sec: 30    # Durum toplama sıklığı
  heartbeat_timeout_sec: 300      # Heartbeat zaman aşımı

load_balancing:
  overload_threshold_pct: 90      # Aşırı yük eşiği
  rebalance_trigger_pct: 30       # Dengeleme tetikleme farkı
```

---

## 📁 Proje Yapısı

```
koordinasyon-sistemi/
├── src/
│   ├── __init__.py              # Sistem sabitleri
│   ├── __main__.py              # CLI giriş noktası
│   ├── cli.py                   # Komut satırı aracı
│   ├── models/
│   │   └── __init__.py          # Veritabanı modelleri & şemalar
│   ├── services/
│   │   ├── coordination_engine.py  # Ana koordinasyon motoru
│   │   ├── task_distributor.py     # Görev dağıtım sistemi
│   │   └── message_cascade.py     # Kademeli mesajlaşma
│   ├── api/
│   │   └── main.py              # FastAPI REST API
│   └── utils/
│       └── addressing.py        # Hiyerarşik adres sistemi
├── config/
│   └── settings.yml             # Yapılandırma
├── scripts/
│   └── init_db.sql              # Veritabanı şeması
├── tests/
│   └── test_core.py             # Test suite
├── docs/
├── docker-compose.yml           # Docker orkestrasyon
├── Dockerfile
├── pyproject.toml               # Python proje yapılandırması
└── README.md
```

---

## 🧪 Test

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Belirli test sınıfı
python -m pytest tests/test_core.py::TestNodeAddress -v

# Coverage ile
python -m pytest tests/ -v --cov=src
```

---

## 🌐 Gerçek Dünya Ölçekleme Stratejisi

9 milyar düğümü gerçekten yönetmek için:

### Faz 1: Merkezi (Seviye 0-3) → 1,111 düğüm
- Tek PostgreSQL + Redis
- Tek API sunucusu
- Doğrudan yönetim

### Faz 2: Bölgesel (Seviye 4-6) → 1,111,000 düğüm
- Her L3 düğüm kendi veritabanına sahip
- Kubernetes üzerinde mikro servisler
- Bölgeler arası mesaj kuyruğu (Kafka)

### Faz 3: Dağıtık (Seviye 7-10) → 9,999,888,889 düğüm
- Her L6 düğüm otonom cluster
- P2P ağ üzerinden iletişim
- Blockchain tabanlı görev onaylama
- Edge computing ile yerel karar verme

```
Dağıtım Mimarisi:

L0-L3:  AWS/GCP (Merkezi)        → 1 Cluster
L4-L6:  Bölgesel DC'ler          → 1,000 Cluster
L7-L10: Edge + P2P               → 1,000,000 Cluster
```

---

## 📜 Lisans

MIT License - Hive Coordinator 2024
