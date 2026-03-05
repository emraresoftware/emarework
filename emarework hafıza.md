# 🧠 EMARE WORK — HAFIZA DOSYASI

> 🔗 **Ortak Hafıza:** [`EMARE_ORTAK_HAFIZA.md`](/Users/emre/Desktop/Emare/EMARE_ORTAK_HAFIZA.md) — Tüm Emare ekosistemi, sunucu bilgileri, standartlar ve proje envanteri için bak.


> **Bu dosya, projemizin tüm detaylarını kayıt altında tutar.**
> **Nerede kaldığımızı ve yazılımın ne olduğunu asla unutmamamız için.**
>
> Son Güncelleme: 4 Mart 2026
> Proje Durumu: **🧙‍♂️ YAZILIM DERVİŞLERİ SİSTEMİ HAZIR — DASHBOARD AKTIF**

---

## 📌 PROJE NE?

**Emare Work** — 21 Yazılım Dervişi ile Çalışan Web Tabanlı Proje Koordinasyon Sistemi.

10 kişilik bir yazılım ekibimiz var. Bu 10 kişinin her birinin kendi 10'ar kişilik grubu var. Ve bu yapı **10 seviye derinlikte** tekrarlanıyor. Toplamda **~11.1 Milyar düğüm** kapasitesi var.

**Temel Prensip:** Her düğüm sadece kendi 10 çocuğunu yönetir. Hiç kimse 10'dan fazla kişiyle doğrudan iletişim kurmaz. Bu sayede bir mesaj 10 adımda 9 milyar kişiye ulaşır.

---

## 🧙‍♂️ YENİ KONSEPT: YAZILIM DERVİŞLERİ

**21 Özel Yapay Zeka "Dervişi"** var. Her biri farklı uzmanlık alanlarında görev alıyor:

- **Frontend Dervişleri:** React, Vue, HTML/CSS/JS uzmanları
- **Backend Dervişleri:** Python, Node.js, Go, Rust uzmanları  
- **Veritabanı Dervişleri:** PostgreSQL, MongoDB, Redis uzmanları
- **DevOps Dervişleri:** Docker, Kubernetes, CI/CD uzmanları
- **Full-Stack Dervişleri:** Her şeyden anlayan "usta" dervişler

**Derviş özellikleri:**
- ⭐ **Ustalık Seviyesi** (1-10): Ne kadar yetenekli
- 🎯 **Uzmanlık Alanları**: Hangi teknolojilerde uzman
- 🟢 **Durum**: Hazır / 🟡 Çalışıyor / 🔴 Offline
- 📊 **Yük**: %0-100 arası mevcut iş yükü

**Kullanım:**
1. Yeni proje oluştur
2. Dosyaları sürükle-bırak
3. Her dosyayı bir dervişe ata (otomatik öneri var)
4. Dervişler göreve başlar!

---

## 🖥️ WEB DASHBOARD SİSTEMİ

### 1. Ana Sayfa (`index.html` — 290 satır)
Kullanıcıyı karşılayan başlangıç sayfası:
- **Emare Work** logosu ve açıklama
- İki panel seçeneği:
  - 📊 **Gelişmiş Dashboard** → Tam özellikli kontrol merkezi
  - 🎮 **Basit Kontrol Paneli** → Adım adım görev atama
- Sistem özeti (21 derviş, hiyerarşi, aktif projeler)

### 2. Gelişmiş Dashboard (`advanced-dashboard.html` — 1773 satır)
Tam özellikli kontrol merkezi:

**Sidebar Navigasyon (7 bölüm):**
- 📊 Dashboard (genel durum)
- 📁 Projeler (tüm projeler listesi)
- 🧙‍♂️ Dervişler (21 derviş kartları)
- ✅ Görevler (task management)
- 📈 Analizler (3 tab: genel, derviş metrikleri, zaman çizelgesi)
- 📋 Loglar (gerçek zamanlı terminal)
- 🌙 Tema Toggle (Dark/Light mode)

**Dashboard Ana Ekran:**
- **4 İstatistik Kartı**: Aktif projeler, Aktif dervişler, Tamamlanan görevler, Ortalama süre
- **6 Chart.js Grafiği**:
  1. Görev Trend (Line chart - 7 gün)
  2. Derviş Kullanımı (Doughnut - 🟢 Hazır/🟡 Çalışıyor/🔴 Offline)
  3. Haftalık Trend (Bar chart)
  4. Görev Dağılımı (Pie - priority bazlı)
  5. Performans Karşılaştırma (Radar - top 5 derviş)
  6. Başarı Oranı (Line - 30 gün)

**Yeni Proje Oluştur Modalı (2 adımlı):**

**Adım 1: Proje Bilgileri + Dosya Yükleme**
```html
<!-- Drag & Drop Zone -->
<div id="dropzone">
  <i class="fas fa-cloud-upload-alt"></i>
  <p>📂 Dosyaları buraya sürükleyin veya tıklayın</p>
  <input type="file" multiple>
</div>
<ul id="file-list">
  <!-- Yüklenen dosyalar buraya listelenir -->
  <li>example.py <button>🗑️</button></li>
</ul>
```

**Adım 2: Dosya-Derviş Eşleştirme**
```html
<!-- Her dosya için bir kart -->
<div class="file-assignment-card">
  <h4>📄 example.py</h4>
  <select class="dervis-select">
    <option value="ai-1">🧙‍♂️ Emare Asistan (Python) ⭐⭐⭐⭐⭐</option>
    <!-- 21 derviş seçeneği, otomatik filtreleniyor -->
  </select>
</div>
```

**Otomatik Derviş Önerisi:**
- `.html/.css/.js/.jsx/.tsx/.vue` → Frontend dervişleri önerilir
- `.py/.js/.go/.rs` → Backend dervişleri önerilir
- `.sql/.db` → Veritabanı dervişleri önerilir
- Ustalık seviyesine göre sıralanır (⭐ en yüksek önce)

### 3. Basit Kontrol Paneli (`control-panel.html` — 597 satır)
Adım adım görev atama arayüzü:

**Adım 1: Proje Seç**
- Mevcut projelerden seç veya yeni oluştur
- Proje detayları (isim, açıklama, deadline)

**Adım 2: 🧙‍♂️ Derviş Seç**
- 21 derviş kartları (grid view)
- Her kartta: İsim, uzmanlık, ustalık ⭐, durum 🟢🟡🔴
- Sadece 🟢 Hazır dervişler seçilebilir

**Adım 3: Dervişleri İzle**
- Atanan görevler listesi
- Gerçek zamanlı ilerleme (progress bar)
- **"Dervişler Göreve"** butonu

---

## 📁 PROJE YAPISI

```
/Users/emre/Desktop/Emare/emarework/
├── DESIGN_GUIDE.md                         ← Mimari tasarım rehberi
├── EMARE_AI_COLLECTIVE.md                  ← AI collective dökümantasyonu
├── EMARE_ORTAK_HAFIZA.md                   ← Global hafıza
├── emarework hafıza.md                     ← BU DOSYA
├── hafıza.md                               ← Eski referans
└── koordinasyon-sistemi/                   ← ANA PROJE KLASÖRÜ
    ├── Dockerfile                          ← Docker imajı (Python 3.12-slim)
    ├── README.md                           ← Proje dökümantasyonu
    ├── EMAREULAK_READY.md                  ← Ulak sistemi bilgileri
    ├── docker-compose.yml                  ← Tam dağıtık ortam
    ├── pyproject.toml                      ← Python paket tanımı
    ├── start_api.sh                        ← API başlatma scripti
    ├── test_100_projects.py                ← 100 proje test senaryosu
    ├── config/
    │   ├── settings.yml                    ← Sistem yapılandırması
    │   └── test_100_projects.yml           ← Test yapılandırması
    ├── scripts/
    │   └── init_db.sql                     ← PostgreSQL şema oluşturma
    ├── tests/
    │   └── test_core.py                    ← Unit testler
    ├── docs/                               ← Dökümantasyon
    └── src/                                ← KAYNAK KOD
        ├── __init__.py                     ← Sabitler
        ├── __main__.py                     ← Modül giriş noktası
        ├── cli.py                          ← CLI aracı
        ├── sim_runner.py                   ← Simülasyon CLI
        ├── emare_workers.py                ← 🧙‍♂️ 21 Derviş tanımları (YENİ)
        ├── project_splitter.py             ← Proje dosya bölme (YENİ)
        ├── project_orchestrator.py         ← Görev orkestrasyon (YENİ)
        ├── celery_app.py                   ← Celery yapılandırma (YENİ)
        ├── emareulak_bridge.py             ← Ulak entegrasyonu
        ├── tasks.py                        ← Celery task'ları (YENİ)
        ├── api/
        │   ├── __init__.py
        │   ├── main.py                     ← 🚀 FastAPI REST API (~850+ satır)
        │   └── static/                     ← 🌐 Web Dashboard (YENİ)
        │       ├── index.html              ← Ana sayfa (290 satır)
        │       ├── control-panel.html      ← Basit panel (597 satır)
        │       └── advanced-dashboard.html ← Gelişmiş dashboard (1773 satır)
        ├── models/
        │   └── __init__.py                 ← SQLAlchemy + Pydantic modelleri
        ├── services/
        │   ├── __init__.py
        │   ├── coordination_engine.py      ← Koordinasyon motoru
        │   ├── task_distributor.py         ← Görev dağıtım sistemi
        │   ├── message_cascade.py          ← Kademeli mesajlaşma
        │   └── year_simulation.py          ← 1 yıl proje simülasyonu
        └── utils/
            └── addressing.py               ← Hiyerarşik adres sistemi
```

**Toplam kaynak kodu: ~6,500+ satır Python + HTML + SQL + YAML**

---

## 🔧 TEKNİK ALTYAPI

### Çalışma Ortamı
- **İşletim Sistemi:** macOS
- **Python:** 3.11+ (venv: `/Users/emre/Desktop/Emare/emarework/.venv/bin/python3`)
- **Virtual Environment:** `/Users/emre/Desktop/Emare/emarework/.venv/`
- **Çalışma Dizini:** `/Users/emre/Desktop/Emare/emarework/koordinasyon-sistemi/`
- **API Sunucusu:** `http://localhost:8000`

### Yüklü Paketler (venv'de)
- `fastapi` — REST API framework
- `uvicorn` — ASGI sunucu
- `sqlalchemy` — ORM / Veritabanı modelleri
- `pydantic` + `pydantic-settings` — Veri doğrulama ve config
- `rich` — Zengin terminal çıktısı
- `structlog` — Yapısal loglama
- `celery` — Asenkron görev kuyruğu
- `redis` — Cache ve mesaj broker
- `pytest` + `pytest-asyncio` — Test framework

### Frontend Teknolojileri
- **Chart.js 4.4.0** — İnteraktif grafikler (6 farklı chart tipi)
- **Font Awesome 6.5.1** — İkon sistemi
- **Vanilla JavaScript** — Framework yok, pür JS
- **CSS Custom Properties** — Tema sistemi (dark/light mode)
- **HTML5 File API** — Drag & drop, FileReader

### Docker Altyapısı (Production için)
- **PostgreSQL 16** — Ana veritabanı
- **Redis 7** — Mesaj kuyruğu + cache
- **Celery Workers** — Asenkron derviş görevleri
- **API Server** — FastAPI + uvicorn (port 8000)

---

## 🏗️ MODÜL DETAYLARI

### 1. 🧙‍♂️ Yazılım Dervişleri Sistemi (`src/emare_workers.py`)

21 farklı AI derviş tanımı — her biri farklı uzmanlık ve yetenekte:

**Derviş veri yapısı:**
```python
@dataclass
class AIWorker:
    worker_id: str          # "ai-1", "ai-2", ... "ai-21"
    name: str               # "🧙‍♂️ Emare Asistan"
    expertise: list[str]    # ["python", "fastapi", "backend"]
    priority: int           # 1-10 (ustalık seviyesi)
    status: str             # "available", "busy", "offline"
    current_load: int       # %0-100 arası yük
    tasks_completed: int    # Toplam tamamlanan görev
    avg_time_minutes: float # Ortalama görev süresi
```

**Derviş kategorileri:**
- **Frontend Uzmanları** (6 derviş): React, Vue, HTML/CSS, TypeScript
- **Backend Uzmanları** (5 derviş): Python, Node.js, Go, Rust, Java
- **Veritabanı Uzmanları** (3 derviş): PostgreSQL, MongoDB, Redis
- **DevOps Uzmanları** (3 derviş): Docker, Kubernetes, CI/CD
- **Full-Stack Masters** (4 derviş): Her alanda yetkin

**Kullanım:**
```python
from src.emare_workers import get_workforce, assign_task, get_available_workers

workers = get_workforce()  # 21 derviş
available = get_available_workers()  # Sadece uygun olanlar
assign_task(worker_id="ai-1", task_id="T-123")
```

### 2. Proje Bölme Sistemi (`src/project_splitter.py`)

Büyük projeleri dosyalara ayırır ve dervişlere dağıtır:

**Kullanım:**
```python
from src.project_splitter import split_project_to_files

files = split_project_to_files(
    project_name="Web Dashboard",
    file_list=["index.html", "app.py", "styles.css"],
    description="Modern web uygulaması"
)
```

**Çıktı:**
```python
[
    {
        "file_id": "F-001",
        "name": "index.html",
        "type": "frontend",
        "size_kb": 25,
        "recommended_workers": ["ai-1", "ai-2", "ai-3"]  # Frontend dervişler
    },
    ...
]
```

### 3. Proje Orkestrasyon (`src/project_orchestrator.py`)

Dosya→Derviş eşleştirme ve görev yönetimi:

**Kullanım:**
```python
from src.project_orchestrator import assign_files_to_workers, monitor_progress

assignments = assign_files_to_workers(
    files=["app.py", "api.py", "db.py"],
    workers=["ai-1", "ai-5", "ai-12"]
)

progress = monitor_progress(project_id="P-123")
# → {"completed": 5, "in_progress": 3, "pending": 2, "percentage": 50.0}
```

### 4. REST API (`src/api/main.py` — ~850+ satır)

FastAPI tabanlı tam özellikli backend. **Tüm endpoint'ler:**

#### 🌐 Genel Endpoint'ler

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/` | GET | Ana sayfa (index.html) |
| `/dashboard` | GET | Gelişmiş dashboard UI |
| `/control-panel` | GET | Basit kontrol paneli UI |
| `/status` | GET | API sistem durumu |
| `/hierarchy` | GET | Hiyerarşi seviye özeti |

#### 🧙‍♂️ Derviş Yönetimi

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/workers` | GET | Tüm 21 derviş listesi |
| `/workers/{id}` | GET | Derviş detayları |
| `/workers/available` | GET | Uygun dervişler (status=available) |
| `/workers/stats` | GET | Derviş istatistikleri (kategori, durum) |
| `/workers/{id}/assign` | POST | Dervişe görev ata |
| `/workers/{id}/complete` | POST | Derviş görevini tamamla |

#### 📁 Proje Yönetimi

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/projects` | GET | Tüm projeler |
| `/projects` | POST | Yeni proje oluştur (dosya atamaları ile) |
| `/projects/{id}` | GET | Proje detayı |
| `/projects/{id}` | PUT | Proje güncelle |
| `/projects/{id}` | DELETE | Proje sil |
| `/projects/{id}/files` | GET | Proje dosyaları |
| `/projects/{id}/timeline` | GET | Gantt chart verisi |
| `/projects/{id}/progress` | GET | İlerleme durumu |

#### ✅ Görev Yönetimi

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/tasks` | POST | Yeni görev oluştur |
| `/tasks/{uid}` | GET | Görev detayı |
| `/tasks/{uid}/tree` | GET | Görev ağacı (alt görevler) |
| `/tasks/{uid}/complete` | POST | Görevi tamamla |
| `/tasks/{uid}/fail` | POST | Görevi başarısız işaretle |
| `/nodes/{address}/tasks` | GET | Düğüme atanan görevler |

#### 💬 Mesajlaşma Sistemi

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/messages/directive` | POST | Yukarıdan aşağı emir |
| `/messages/broadcast` | POST | Toplu yayın |
| `/messages/report` | POST | Aşağıdan yukarı rapor |
| `/nodes/{address}/inbox` | GET | Gelen kutusu |

#### 📊 Analitik & Dashboard

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/analytics/overview` | GET | Genel sistem özeti |
| `/analytics/summary` | GET | Dashboard metrikleri (son 30 gün) |
| `/analytics/subtree/{address}` | GET | Alt ağaç analitik |
| `/analytics/health/{address}` | GET | Sağlık kontrolü |
| `/analytics/rebalance/{address}` | POST | Yük dengeleme |
| `/ecosystem/overview` | GET | Tam ekosistem durumu |

#### 🔧 Yönetim Endpoint'leri

| Endpoint | Metot | Açıklama |
|----------|-------|----------|
| `/nodes` | POST | Yeni düğüm kaydet |
| `/nodes/{address}` | GET | Düğüm bilgisi |
| `/nodes/{address}/children` | GET | Çocuk düğümler |
| `/nodes/{address}/heartbeat` | POST | Yaşam sinyali |
| `/nodes/{address}/status` | PUT | Durum güncelle |
| `/batch/register-tree` | POST | Toplu düğüm kaydı |

**Swagger UI:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`

### 5. Hiyerarşik Adres Sistemi (`src/utils/addressing.py` — 223 satır)

Eski "Hive Coordinator" altyapısından miras — 10 seviye derinlikte hiyerarşik düğüm sistemi.

Her düğüm benzersiz bir adresle tanımlanır:

```
Adres formatı: "L{seviye}.{indeks0}.{indeks1}...{indeksN}"
Örnekler:
  L0           → Kök lider
  L1.3         → Seviye 1, 4. takım lideri (0-indexed)
  L3.0.4.7     → Seviye 3, kök→dal0→dal4→dal7
```

**Kullanım:**
```python
from src.utils.addressing import NodeAddress

addr = NodeAddress.from_string("L2.0.5")
print(addr.parent)           # L1.0
print(addr.children)         # [L3.0.5.0, L3.0.5.1, ..., L3.0.5.9]
print(addr.subtree_size)     # 1111 düğüm
```

### 6. Koordinasyon Motoru (`src/services/coordination_engine.py` — 449 satır)

Hiyerarşideki tüm koordinasyon işlemlerini yönetir:

**Kullanım:**
```python
from src.services.coordination_engine import CoordinationEngine

engine = CoordinationEngine()
await engine.register_node("L0", name="Genel Koordinatör")
await engine.heartbeat("L0")
stats = await engine.aggregate_subtree_stats("L0")
least = await engine.find_least_loaded_child("L0")
await engine.rebalance_subtree("L0")
```

### 7. Görev Dağıtım Sistemi (`src/services/task_distributor.py` — 432 satır)

Görevleri hiyerarşi boyunca akıllıca dağıtır.

**Dağıtım stratejileri:**
- **CASCADE**: Her seviyede 10'a böl (L0→L1(10)→L2(100)→...)
- **TARGETED**: Belirli düğüme doğrudan atama
- **BROADCAST**: Tüm alt ağaca kopyala
- **WEIGHTED**: Yüke göre orantılı dağıt

### 8. Kademeli Mesajlaşma (`src/services/message_cascade.py` — 359 satır)

9 milyar düğüm arasında verimli iletişim:
- **DIRECTIVE**: Yukarı→Aşağı emir
- **REPORT**: Aşağı→Yukarı rapor
- **BROADCAST**: Tüm alt ağaca yayın
- **PEER**: Eşler arası mesaj
- **ESCALATION**: Sorunları köke ilet

### 9. Celery Entegrasyonu (`src/celery_app.py` + `src/tasks.py`)

Asenkron görev işleme altyapısı:

**Celery task'ları:**
```python
# src/tasks.py
@celery_app.task
def process_file_async(file_id, worker_id):
    """Derviş dosyayı işler (async)"""
    ...

@celery_app.task
def aggregate_progress(project_id):
    """Proje ilerlemesini topla"""
    ...
```

**Kullanım:**
```python
from src.tasks import process_file_async

# Asenkron görev başlat
task = process_file_async.delay(file_id="F-123", worker_id="ai-5")
print(task.id)  # Task ID'si
```

### 6. CLI Aracı (`src/cli.py` — 417 satır)

Rich kütüphanesiyle zengin terminal arayüzü. **Artık opsiyonel** — web dashboard kullanımı öneriliyor.

**Komutlar:**
```bash
python -m src.cli overview          # Hiyerarşi seviye tablosu
python -m src.cli tree [N]          # Ağaç görünümü (derinlik N)
python -m src.cli simulate          # Demo simülasyonu (7 adımlık)
python -m src.cli serve [PORT]      # API sunucusu başlat
```

### 7. Yıllık Simülasyon Motoru (`src/services/year_simulation.py` — 814 satır)

100 GB kod projesini simüle eder. **Test amaçlı** — production'da kullanılmıyor.

### 8. Veritabanı Modelleri (`src/models/__init__.py` — 309 satır)

**SQLAlchemy tabloları:**
- `nodes` — Hiyerarşik düğümler (L0-L10)
- `tasks` — Görevler (parent-child ilişkili)
- `messages` — Mesajlar (cascade tracking)
- `aggregated_metrics` — Periyodik metrikler
- `projects` — Proje bilgileri (YENİ)
- `files` — Proje dosyaları (YENİ)
- `workers` — AI dervişler (YENİ)

**Pydantic şemaları (API validasyonu):**
- `NodeCreate`, `NodeResponse`
- `TaskCreate`, `TaskResponse`
- `MessageCreate`
- `ProjectCreate`, `ProjectResponse` (YENİ)
- `WorkerResponse` (YENİ)

### 9. PostgreSQL Şeması (`scripts/init_db.sql` — 135+ satır)

- Partitioned `nodes` tablosu (level bazlı)
- Optimize indeksler (B-tree, GIN)
- Foreign key constraints
- Trigger'lar (update_timestamp)

### 10. Unit Testler (`tests/test_core.py` — 275 satır)

**28 test, tümü PASSED ✅:**
- NodeAddress (12 test)
- CoordinationEngine (5 test)
- TaskDistributor (3 test)
- MessageCascade (5 test)
- Helpers (3 test)

---

## 🖥️ ÇALIŞTIRMA KOMUTLARI

### Hızlı Başlangıç (Yerel)

```bash
# Proje dizinine git
cd "/Users/emre/Desktop/Emare/emarework/koordinasyon-sistemi"

# Virtual environment Python'ı
PYTHON="/Users/emre/Desktop/Emare/emarework/.venv/bin/python3"

# API sunucusu başlat (Önerilen)
$PYTHON -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# VEYA start script ile
./start_api.sh

# → http://localhost:8000              (Ana sayfa)
# → http://localhost:8000/dashboard    (Gelişmiş Dashboard 🧙‍♂️)
# → http://localhost:8000/control-panel (Basit Panel)
# → http://localhost:8000/docs         (Swagger UI)
# → http://localhost:8000/redoc        (ReDoc)

# CLI Komutları
$PYTHON -B -m src.cli overview          # Hiyerarşi seviye tablosu
$PYTHON -B -m src.cli tree 3            # Ağaç görünümü (3 seviye)
$PYTHON -B -m src.cli simulate          # Demo simülasyon

# Testleri çalıştır
$PYTHON -B -m pytest tests/test_core.py -v
```

### Docker ile Production

```bash
cd "/Users/emre/Desktop/Emare/emarework/koordinasyon-sistemi"

# Tüm servisleri başlat
docker-compose up -d

# Logları izle
docker-compose logs -f api

# Durdur
docker-compose down
```

---

## 🔄 NEREDE KALDIK? (4 Mart 2026)

### Tamamlanan İşler ✅

#### Faz 1: Backend Altyapı (Tamamlandı)
1. **FastAPI REST API** — ~850+ satır, 40+ endpoint
2. **Hiyerarşik düğüm sistemi** — 10 seviye, 11.1 milyar düğüm kapasiteli
3. **Koordinasyon motoru** — Yük dengeleme, sağlık kontrolü
4. **Görev dağıtım sistemi** — Cascade, targeted, broadcast, weighted
5. **Kademeli mesajlaşma** — 5 mesaj tipi, 9 milyar düğüme ulaşım
6. **Yıllık simülasyon motoru** — 365 gün, dinamik hiyerarşi
7. **PostgreSQL şeması** — Partitioned tablolar
8. **Unit testler** — 28 test, hepsi PASSED
9. **Docker altyapısı** — PostgreSQL + Redis + Celery

#### Faz 2: Web Dashboard (4 Mart 2026 - Tamamlandı ✅)
10. **🧙‍♂️ 21 Yazılım Dervişi Sistemi** — Her biri farklı uzmanlık ve ustalık
11. **Ana Sayfa (index.html — 290 satır)** — Karşılama + panel seçimi
12. **Gelişmiş Dashboard (advanced-dashboard.html — 1773 satır)**:
    - ✅ Sidebar navigasyon (7 bölüm)
    - ✅ 4 istatistik kartı (gerçek zamanlı)
    - ✅ 6 Chart.js grafiği (line, doughnut, bar, pie, radar)
    - ✅ Tema toggle (🌙 Dark / ☀️ Light)
    - ✅ Projects view (filtreleme + arama)
    - ✅ Workers view (21 derviş kartı)
    - ✅ Tasks view (durum filtreleme)
    - ✅ Analytics (3 tab: genel, derviş, zaman)
    - ✅ Real-time logs (terminal görünümü)
13. **Yeni Proje Oluştur Modal (2 adım):**
    - ✅ Adım 1: Proje bilgileri + **Drag & Drop dosya yükleme**
    - ✅ Adım 2: Her dosya için derviş atama
    - ✅ **Otomatik derviş önerisi** (dosya uzantısına göre)
    - ✅ Expertise-based filtering (frontend/backend/database)
    - ✅ Ustalık bazlı sıralama (⭐⭐⭐⭐⭐ önce)
14. **Basit Kontrol Paneli (control-panel.html — 597 satır)**:
    - ✅ Adım adım proje oluşturma
    - ✅ Derviş seçimi (🟢 Hazır olanlar)
    - ✅ İlerleme takibi
    - ✅ "Dervişler Göreve" butonu
15. **API Endpoint'ler Genişletme:**
    - ✅ `/workers/*` (21 derviş yönetimi)
    - ✅ `/projects/*` (proje CRUD + progress)
    - ✅ `/dashboard` (HTML serve)
    - ✅ `/analytics/summary` (dashboard metrics)
    - ✅ `/workers/stats` (kategori/durum istatistikleri)
    - ✅ `/projects/{id}/timeline` (Gantt chart verisi)
16. **Terminoloji Güncellemesi:**
    - ✅ "AI Worker" → "🧙‍♂️ Yazılım Dervişi"
    - ✅ "Task" → "Görev"
    - ✅ "Priority" → "Ustalık" ⭐
    - ✅ "Available" → "🟢 Hazır"
    - ✅ "Busy" → "🟡 Çalışıyor"
    - ✅ "Offline" → "🔴 Offline"

### Aktif Özellikler (Çalışıyor) 🟢

- ✅ **Port 8000** üzerinde API server aktif
- ✅ **http://localhost:8000/dashboard** — Gelişmiş dashboard erişilebilir
- ✅ **http://localhost:8000/control-panel** — Basit panel erişilebilir
- ✅ **Drag & drop dosya yükleme** — HTML5 FileReader API çalışıyor
- ✅ **Otomatik derviş önerisi** — Dosya uzantısına göre filtreleme
- ✅ **Chart.js grafikleri** — 6 farklı chart tipi render ediliyor
- ✅ **Theme toggle** — localStorage ile persist ediliyor
- ✅ **21 Derviş** — Tüm dervişler `/workers` endpoint'inden geliyor

### Kalan / İyileştirme Gereken İşler 📋

| İş | Öncelik | Durum | Açıklama |
|----|---------|-------|----------|
| **Gerçek dosya yükleme** | 🔴 Yüksek | Pending | Şu an client-side FileReader, server'a upload edilmeli |
| **Dosya→Derviş task oluşturma** | 🔴 Yüksek | Pending | Project modal'dan submit sonrası gerçek task create |
| **Derviş görev işleme** | 🟡 Orta | In Progress | Celery worker'lar hazır, entegre edilmeli |
| **WebSocket real-time updates** | 🟡 Orta | Planned | Görev ilerlemesi için canlı güncellemeler |
| **Gerçek DB bağlantısı** | 🟡 Orta | Partial | In-memory şu an, PostgreSQL'e geçiş |
| **Proje folder creation** | 🟡 Orta | Pending | Filesystem'de gerçek proje klasörü oluşturma |
| **File type validation** | 🟢 Düşük | Pending | Upload sırasında dosya tipi kontrol |
| **Bulk derviş assignment** | 🟢 Düşük | Planned | Tüm dosyalara tek derviş atama |
| **Project templates** | 🟢 Düşük | Idea | Hazır proje şablonları (React, Django, vb.) |
| **JWT Authentication** | 🟢 Düşük | Planned | API güvenliği |
| **Monitoring (Prometheus)** | 🟢 Düşük | Idea | Metrik toplama |

### Frontend İyileştirmeleri (Opsiyonel) 💡

- [ ] File preview modal (yüklenen dosyaları görüntüle)
- [ ] Derviş profil sayfası (detaylı istatistikler)
- [ ] Proje detay sayfası (timeline, commits, tasks)
- [ ] Notification system (toast/alert için)
- [ ] Search & filter iyileştirmeleri
- [ ] Mobile responsive design (bazı bölümlerde)
- [ ] Dark mode color adjustments (bazı grafiklerde)
- [ ] Loading spinners (API call'lar için)

---

## 🗝️ ÖNEMLİ SABİTLER VE REFERANSLAR

```python
# Emare Work Dervişler
TOTAL_DERVISHES = 21        # Toplam derviş sayısı
FRONTEND_EXPERTS = 6        # Frontend uzmanı
BACKEND_EXPERTS = 5         # Backend uzmanı
DATABASE_EXPERTS = 3        # Veritabanı uzmanı
DEVOPS_EXPERTS = 3          # DevOps uzmanı
FULLSTACK_MASTERS = 4       # Full-stack master

# Hiyerarşi (Eski sistem - hala kullanımda)
HIERARCHY_DEPTH = 10        # 10 seviye (L0-L10)
BRANCH_FACTOR = 10          # Her düğüm 10 çocuk
TOTAL_NODES = 11_111_111_111  # ~11.1 Milyar düğüm

# API
API_HOST = "0.0.0.0"
API_PORT = 8000
BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8000/dashboard"
CONTROL_PANEL_URL = "http://localhost:8000/control-panel"
SWAGGER_URL = "http://localhost:8000/docs"
REDOC_URL = "http://localhost:8000/redoc"

# Frontend
CHART_JS_VERSION = "4.4.0"
FONT_AWESOME_VERSION = "6.5.1"
THEME_STORAGE_KEY = "emarework-theme"  # localStorage key

# Docker (Production)
POSTGRES_DB = "hive_coordinator"
POSTGRES_USER = "hive"
POSTGRES_PASSWORD = "hive_secret"
POSTGRES_PORT = 5432
REDIS_URL = "redis://localhost:6379/0"
REDIS_MAX_MEMORY = "512mb"

# Derviş Durumları
STATUS_AVAILABLE = "available"  # 🟢 Hazır
STATUS_BUSY = "busy"            # 🟡 Çalışıyor
STATUS_OFFLINE = "offline"      # 🔴 Offline

# Görev Durumları
TASK_PENDING = "pending"
TASK_ASSIGNED = "assigned"
TASK_IN_PROGRESS = "in_progress"
TASK_REVIEW = "review"
TASK_COMPLETED = "completed"
TASK_FAILED = "failed"
TASK_BLOCKED = "blocked"

# Ustalık Seviyeleri (1-10)
MASTERY_BEGINNER = 1-3      # Başlangıç
MASTERY_INTERMEDIATE = 4-6   # Orta
MASTERY_ADVANCED = 7-8       # İleri
MASTERY_EXPERT = 9-10        # Uzman
```

---

## 📊 MİMARİ DİYAGRAM (Güncel)

```
┌─────────────────────────────────────────────────────────────────┐
│                        EMARE WORK                                │
│            Yazılım Dervişleri Koordinasyon Sistemi              │
├─────────────┬──────────────┬─────────────┬─────────────────────┤
│  WEB UI     │   REST API   │   Backend   │   AI Dervişler      │
│  (HTML/JS)  │   (FastAPI)  │   Services  │   (21 Worker)       │
├─────────────┼──────────────┼─────────────┼─────────────────────┤
│ Dashboard   │ /workers/*   │ Orchestrator│ Frontend (6)        │
│ Control Panel│ /projects/* │ Splitter    │ Backend (5)         │
│ Theme Toggle│ /tasks/*     │ Assignm│ Database (3)        │
│ Chart.js (6)│ /analytics/* │ Engine      │ DevOps (3)          │
│ Drag & Drop │ /messages/*  │ Cascade     │ Full-Stack (4)      │
├─────────────┴──────────────┴─────────────┴─────────────────────┤
│  PostgreSQL (projeler, görevler, düğümler)                      │
│  Redis (cache, queue)                                           │
│  Celery (async task processing)                                 │
└─────────────────────────────────────────────────────────────────┘

                    DERVIŞ WORKFLOW
                    ══════════════════
    
    👤 Kullanıcı
       ↓
    📂 Proje Oluştur + Dosya Yükle (Drag & Drop)
       ↓
    🧙‍♂️ Her dosyayı dervişe ata (otomatik öneri)
       ↓
    📋 Görevler oluşturulur (Celery queue)
       ↓
    🔄 Dervişler dosyaları işler (parallel)
       ↓
    ✅ Sonuçlar toplanır (aggregation)
       ↓
    📊 Dashboard'da ilerleme gösterilir
```

---

## 📝 NOTLAR

- **Python 3.11+** kullanıyoruz (venv içinde)
- `-B` flag'ı: `__pycache__` oluşturmaz
- **Port 8000** varsayılan API portu
- **Dervişler** stateless — her dosya bağımsız işlenir
- **Swagger UI** her zaman güncel — API docs otomatik
- **Chart.js** CDN'den yükleniyor (offline çalışmaz)
- **localStorage** tema tercihini saklar
- **Drag & drop** modern tarayıcılarda çalışır (IE desteksiz)
- **21 sayısı** Fibonacci'den geliyor (3, 5, 8, 13, **21**)
- **Derviş** metaforu: "Teknoloji ustası, sürekli dönen, gezen bilge"

---

## 🚀 SONRAKI ADIMLAR

1. **Gerçek dosya upload implementasyonu** (FormData + multipart/form-data)
2. **Derviş task execution** (Celery worker'ları tetikle)
3. **WebSocket canlı güncellemeler** (Socket.io veya native WebSocket)
4. **PostgreSQL tam entegrasyonu** (şu an in-memory)
5. **Production deployment** (Docker Compose + Nginx)
6. **Monitoring & Logging** (Sentry + Prometheus)
7. **Authentication** (JWT token sistemi)

---

> 💡 **Bu dosyayı her büyük değişiklikte güncelle.**  
> Projeyi 6 ay sonra açtığında bile hemen nereden devam edeceğini bil!
