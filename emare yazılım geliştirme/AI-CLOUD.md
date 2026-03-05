# 🤖 AI-CLOUD — Yazılım Geliştirme Önerileri

> **Proje:** EmareCloud — Infrastructure Management  
> **Uzmanlık:** Flask + SSH + LXD + Firewall + Docker  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Her Proje LXD Container'da Çalışmalı

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm production deployments

### Sorun
Projeler doğrudan host makinede çalışıyor. Bir proje çöktüğünde diğerlerini etkiliyor. Port çakışmaları, library version çatışmaları yaşanıyor.

### Öneri
Her Emare projesi kendi **LXD container**'ında izole çalışsın. Merkezi yönetim EmareCloud üzerinden yapılsın.

### Container Yapısı
```bash
# Her proje için container oluştur
lxc launch ubuntu:22.04 emare-finance
lxc launch ubuntu:22.04 emare-cloud
lxc launch ubuntu:22.04 emare-asistan
# ...

# Port yönlendirme
lxc config device add emare-finance port8000 proxy \
    listen=tcp:0.0.0.0:8000 connect=tcp:127.0.0.1:8000
```

### Geliştirme Adımları
1. [ ] EmareCloud'a "Proje Konteyneri Oluştur" butonu ekle
2. [ ] Her proje için standart container template
3. [ ] Otomatik health check + restart
4. [ ] Resource limiting (CPU/RAM per container)
5. [ ] Backup: günlük LXD snapshot

### Beklenen Sonuç
%100 proje izolasyonu, sıfır port/library çakışması

---

## [4 Mart 2026] — Merkezi Log Toplayıcı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Tüm projeler → Emare Log

### Sorun
21 projenin logları farklı yerlerde. Sorun çıktığında manuel araştırma gerekiyor.

### Öneri
Her container syslog'un Emare Log'a gönderir. Emare Log merkezi dashboard ile analiz eder.

### Config Örneği
```bash
# Her container'da /etc/rsyslog.conf
*.* @@emare-log-server:514
```

### Beklenen Sonuç
Merkezi log analizi, AI ile anomaly detection, anlık alarm

---

## [4 Mart 2026] — Emare Marketplace Entegrasyonu

**Öncelik:** 🟡 Orta  
**Kapsam:** Tüm projeler → EmareCloud Marketplace

### Sorun
42 hazır uygulama var EmareCloud Marketplace'de ama Emare projeleri bunu kullanmıyor.

### Öneri  
Emare projelerinin de Marketplace'e eklenmesi. Her proje bir tıkla diğer sunuculara deploy edilebilsin.

### Geliştirme Adımları
1. [ ] Her proje için Marketplace manifest dosyası (`marketplace.json`)
2. [ ] One-click deploy scripti
3. [ ] Versiyon yönetimi (semver)
4. [ ] Dependency graph (hangi proje hangisine bağlı)
