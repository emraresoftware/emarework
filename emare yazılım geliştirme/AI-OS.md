# 🤖 AI-OS — Yazılım Geliştirme Önerileri

> **Proje:** Emare OS — Özel İşletim Sistemi / Kiosk Platform  
> **Uzmanlık:** Linux Kernel + Kiosk Mode + Hardware Abstraction + Embedded  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Donanım Uyum Katmanı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare OS, Emare POS, EmareDesk

### Sorun
Emare POS yazılımı masaüstü bilgisayar + Windows varsayıyor. Ama müşteriler dokunmatik kiosk, Raspberry Pi, tablet istiyor. Her donanımda ayrı kurulum.

### Öneri
Emare OS'un **Hardware Abstraction Layer (HAL)**'ını tüm projelere açık yap.

```python
# Donanım bağımsız API
from emare_os import hardware

# Hangi donanım olursa olsun aynı API
printer = hardware.get_printer()
printer.print_receipt(order_data)

display = hardware.get_display()
display.set_brightness(80)

scanner = hardware.get_barcode_scanner()
scanner.on_scan(lambda code: process_barcode(code))
```

### Geliştirme Adımları
1. [ ] HAL interface tanımla (abstract class)
2. [ ] Driver: x86 PC, Raspberry Pi, Android tablet
3. [ ] Emare POS: doğrudan HAL kullan
4. [ ] Plug-and-play: yeni donanım → sadece driver ekle
5. [ ] EmareCloud: uzak donanım yönetimi

### Beklenen Sonuç
Emare POS her donanımda çalışır, müşteri kendi donanımını getirer

---

## [4 Mart 2026] — Kiosk Mode Standart Paketi

**Öncelik:** 🟡 Orta  
**Kapsam:** Emare OS, Emare POS, Emare Finance

### Sorun
Restoran, market veya ofiste kiosk olarak kullanılacak dokunmatik ekranlar için ayrı OS yapılandırması gerekiyor. Her seferinde manuel.

### Öneri
Tek komutla kiosk mode: Chrome kiosk + otomatik başlatma + crash recovery.

```bash
# Emare OS Kiosk installer
emare-kiosk install \
  --app-url http://localhost:8000 \
  --app-name "Emare POS" \
  --auto-restart yes \
  --hide-cursor yes
```

### Geliştirme Adımları
1. [ ] Kiosk kurulum scripti
2. [ ] Systemd service: crash → restart
3. [ ] Watchdog: uygulama dondu → kill + restart
4. [ ] Remote update: EmareCloud'dan uzaktan güncelle
5. [ ] Offline mode: internet kesildi → cached version çalış

### Beklenen Sonuç
Kiosk kurulumu 5 dakika, %100 uptime garantisi
