# 🤖 AI-SIBER — Yazılım Geliştirme Önerileri

> **Proje:** SiberEmare — Siber Güvenlik Platformu  
> **Uzmanlık:** Pentest + Vulnerability Scanner + SIEM + Threat Intel  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Ekosistemi Güvenlik Taraması

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
21 projenin güvenlik durumu bilinmiyor. Hangi projede açık var? Hangi dependency'de CVE var? Kimse bilmiyor.

### Öneri
Haftalık otomatik güvenlik taraması: tüm Emare projelerini tara, raporu Hub'a gönder.

### Tarama Kapsamı
```bash
# Her proje için çalışacak:
1. Dependency check (pip audit, composer audit, npm audit)
2. SAST (bandit, semgrep)
3. Secret scanning (truffleHog - API key var mı?)
4. Port scan (nmap)
5. CVE veritabanı kontrolü
```

### Geliştirme Adımları
1. [ ] scheduler.py ile haftalık cron
2. [ ] projects.json'dan proje listesi al
3. [ ] Her proje için paralel tarama
4. [ ] Rapor: JSON → Hub API → Dashboard
5. [ ] Kritik buluşta WhatsApp + e-posta alarm

### Beklenen Sonuç
21 projenin güvenlik skoru dashboard'da, sıfır kör nokta

---

## [4 Mart 2026] — Hardcoded Secret Tespit Sistemi

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler (git hook ile)

### Sorun
Anayasa Madde 6 ihlalleri: projeler commit atarken API key, şifre, token .py/.js dosyalarına gömüyor.

### Öneri
Git pre-commit hook: commit öncesi otomatik secret scan.

```bash
# .git/hooks/pre-commit
#!/bin/bash
python3 /Users/emre/Desktop/Emare/SiberEmare/secret_scanner.py \
    --path . \
    --fail-on-found

if [ $? -ne 0 ]; then
    echo "🔴 Hardcoded secret tespit edildi! Commit iptal."
    exit 1
fi
```

### Pattern'lar
```python
PATTERNS = [
    r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{8,}',
    r'sk_live_[a-zA-Z0-9]+',  # Stripe key
    r'AIza[0-9A-Za-z-_]{35}',  # Google API key
    r'(?i)api[_-]?key\s*=\s*["\'][^"\']+',
]
```

### Geliştirme Adımları
1. [ ] secret_scanner.py yaz
2. [ ] Pre-commit hook scripti + dağıt (tüm projelere)
3. [ ] Whitelist: test dosyaları için istisna
4. [ ] Merkezi rapor: haftalık "geçen commitlerdeki sorunlar"

### Beklenen Sonuç
Hiçbir Emare projesinde hardcoded credential kalmaz
