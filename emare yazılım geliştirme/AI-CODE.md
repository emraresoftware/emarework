# 🤖 AI-CODE — Yazılım Geliştirme Önerileri

> **Proje:** Emare Code — AI Destekli Code Editor & IDE  
> **Uzmanlık:** LSP + Code Intelligence + AI Completion + Refactoring  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Kod Standartları Enforcer

**Öncelik:** 🔴 Kritik  
**Kapsam:** Emare Code, Tüm projeler

### Sorun
21 proje farklı kod formatında yazılıyor. Python projelerinde PEP8 uyumu yok, Laravel'de PSR standartları uygulanmıyor. Code review'da çok vakit harcanıyor.

### Öneri
Emare Code'un analiz motorunu CI/CD'ye entegre et: her commit'te otomatik format + lint kontrolü.

```yaml
# .github/workflows/emare-code-check.yml
- name: Emare Code Quality Check
  run: |
    # Python projeleri
    ruff check . --select E,W,F
    black --check .
    mypy . --strict
    
    # PHP projeleri  
    ./vendor/bin/pint --test
    
    # JS projeleri
    eslint . --ext .js,.ts
    prettier --check .
```

### Geliştirme Adımları
1. [ ] Dil tespiti: proje tipine göre doğru linter
2. [ ] Pre-commit hook: commit öncesi format check
3. [ ] Auto-fix: mümkünse otomatik düzelt
4. [ ] Rapor: hangi dosyada kaç ihlal
5. [ ] Emare Hub: kod kalitesi skoru dashboard

### Beklenen Sonuç
Tüm projeler tutarlı format, code review %50 daha hızlı

---

## [4 Mart 2026] — Emare Kod Şablonları Kütüphanesi

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare Code, EmareSetup

### Sorun
Geliştiriciler (AI'lar dahil) aynı pattern'leri tekrar tekrar yazıyor. Auth middleware, pagination, error handler her projede farklı.

### Öneri
Emare Code içinde onaylı **Snippet Kütüphanesi**: bir tuşla proje için doğru snippeti ekle.

### Snippet Kategorileri
```
emare-snippets/
├── fastapi/
│   ├── auth-middleware.py
│   ├── pagination.py
│   ├── error-handler.py
│   └── health-check.py
├── laravel/
│   ├── base-controller.php
│   ├── api-response.php
│   └── rate-limiter.php
└── javascript/
    ├── api-client.js
    ├── error-boundary.jsx
    └── form-handler.js
```

### Geliştirme Adımları
1. [ ] Snippet formatı standartlaştır
2. [ ] Tüm projelerden ortak pattern'leri çıkar
3. [ ] EMARE_ORTAK_CALISMA'ya snippet kütüphanesi ekle
4. [ ] Emare Code: snippet arama ve ekleme UI
5. [ ] Semver: snippet'ler versiyonlandı

### Beklenen Sonuç
Boilerplate yazma sıfır, tüm projeler aynı kaliteli temel kod
