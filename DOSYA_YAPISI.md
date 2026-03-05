# 📁 Hive Coordinator — Dosya Yapısı

> **Oluşturulma:** Otomatik  
> **Amaç:** Yapay zekalar kod yazmadan önce mevcut dosya yapısını incelemeli

---

## Proje Dosya Ağacı

```
/Users/emre/Desktop/Emare/emarework
├── DESIGN_GUIDE.md
├── EMARE_AI_COLLECTIVE.md
├── EMARE_ORTAK_CALISMA -> /Users/emre/Desktop/Emare/EMARE_ORTAK_CALISMA
├── EMARE_ORTAK_HAFIZA.md
├── hafıza.md
└── koordinasyon-sistemi
    ├── .env
    ├── .env.example
    ├── .pylintrc
    ├── .pytest_cache
    │   ├── .gitignore
    │   ├── CACHEDIR.TAG
    │   ├── README.md
    │   └── v
    │       └── cache
    ├── .vscode
    │   └── settings.json
    ├── BUGFIX.md
    ├── Dockerfile
    ├── EMAREULAK_READY.md
    ├── PRODUCTION_READY.md
    ├── README.md
    ├── config
    │   ├── settings.yml
    │   └── test_100_projects.yml
    ├── docker-compose.yml
    ├── docs
    ├── py.typed
    ├── pyproject-typecheck.toml
    ├── pyproject.toml
    ├── pyrightconfig.json
    ├── requirements.txt
    ├── scripts
    │   └── init_db.sql
    ├── src
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── api
    │   │   ├── __init__.py
    │   │   ├── main.py
    │   │   └── static
    │   ├── cache.py
    │   ├── celery_app.py
    │   ├── cli.py
    │   ├── config.py
    │   ├── db
    │   │   ├── __init__.py
    │   │   ├── database.py
    │   │   ├── models.py
    │   │   └── repository.py
    │   ├── emare_workers.py
    │   ├── emareulak_bridge.py
    │   ├── models
    │   │   └── __init__.py
    │   ├── project_orchestrator.py
    │   ├── project_splitter.py
    │   ├── services
    │   │   ├── __init__.py
    │   │   ├── coordination_engine.py
    │   │   ├── message_cascade.py
    │   │   ├── task_distributor.py
    │   │   └── year_simulation.py
    │   ├── sim_runner.py
    │   ├── tasks.py
    │   └── utils
    │       ├── __init__.py
    │       └── addressing.py
    ├── start_api.sh
    ├── start_dev.sh
    ├── test_100_projects.py
    ├── test_imports.py
    └── tests
        └── test_core.py

18 directories, 56 files

```

---

## 📌 Kullanım Talimatları (AI İçin)

Bu dosya, kod üretmeden önce projenin mevcut yapısını kontrol etmek içindir:

1. **Yeni dosya oluşturmadan önce:** Bu ağaçta benzer bir dosya var mı kontrol et
2. **Yeni klasör oluşturmadan önce:** Mevcut klasör yapısına uygun mu kontrol et
3. **Import/require yapmadan önce:** Dosya yolu doğru mu kontrol et
4. **Kod kopyalamadan önce:** Aynı fonksiyon başka dosyada var mı kontrol et

**Örnek:**
- ❌ "Yeni bir auth.py oluşturalım" → ✅ Kontrol et, zaten `app/auth.py` var mı?
- ❌ "config/ klasörü oluşturalım" → ✅ Kontrol et, zaten `config/` var mı?
- ❌ `from utils import helper` → ✅ Kontrol et, `utils/helper.py` gerçekten var mı?

---

**Not:** Bu dosya otomatik oluşturulmuştur. Proje yapısı değiştikçe güncellenmelidir.

```bash
# Güncelleme komutu
python3 /Users/emre/Desktop/Emare/create_dosya_yapisi.py
```
