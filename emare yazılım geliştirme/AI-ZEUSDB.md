# 🤖 AI-ZEUSDB — Yazılım Geliştirme Önerileri

> **Proje:** ZeusDB / EmareOracle — Distributed Database Sistemi  
> **Uzmanlık:** PostgreSQL + Distributed Systems + Replication + Sharding  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Veritabanı Standardı

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
Her proje farklı DB kullanıyor: SQLite, PostgreSQL, MySQL, MongoDB. Yedekleme, monitoring, migration stratejileri çelişiyor.

### Öneri
**PostgreSQL standart DB** olmalı. SQLite sadece POS gibi offline-first için. Mongo sadece log/event için.

### Migration Yol Haritası
```sql
-- Her projenin uyması gereken tablo standardı
CREATE TABLE base_model (
    id          BIGSERIAL PRIMARY KEY,
    uuid        UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at  TIMESTAMPTZ  -- soft delete
);
```

### Geliştirme Adımları
1. [ ] Her proje için PostgreSQL migration kılavuzu
2. [ ] Alembic (Python) veya Laravel Migrations şablon
3. [ ] Row-level security: tenant bazlı erişim
4. [ ] pg_partman: büyük tablolar için partitioning
5. [ ] pgBackRest: otomatik yedekleme

### Beklenen Sonuç
Tek DB standardı = ortak monitoring, backup, scaling stratejisi

---

## [4 Mart 2026] — Read Replica ile Okuma Ölçekleme

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare Finance, EmareCloud, Hive Coordinator

### Sorun
Yoğun okuma işlemleri primary DB'yi yavaşlatıyor. Raporlar, dashboardlar anlık görünüyor gibi ama aslında gecikiyor.

### Öneri
Primary → 1+ Read Replica. Yazma: primary, Okuma: replica.

```python
# SQLAlchemy ile read/write splitting
engine_write = create_engine(POSTGRES_PRIMARY_URL)
engine_read = create_engine(POSTGRES_REPLICA_URL)

with Session(engine_read) as session:
    invoices = session.query(Invoice).filter(...).all()
```

### Geliştirme Adımları
1. [ ] PostgreSQL streaming replication kur
2. [ ] EmareCloud'da replica container
3. [ ] Uygulama katmanı: read/write routing
4. [ ] Monitoring: replication lag uyarısı

### Beklenen Sonuç
%50 daha hızlı dashboard yüklenme, primary DB rahatlar
