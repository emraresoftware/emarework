# 🤖 AI-LOG — Yazılım Geliştirme Önerileri

> **Proje:** Emare Log — ISS Log Yönetim Sistemi  
> **Uzmanlık:** MikroTik + netflow + Radius + Log Analizi + Scraping  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Merkezi Log Altyapısı (Tüm Projeler İçin)

**Öncelik:** 🔴 Kritik  
**Kapsam:** Tüm projeler

### Sorun
21 proje kendi konsol/dosya loglamasını yapıyor. Sorun çıkınca hangi projede ne hata olduğunu anlamak için tek tek sunucuya bağlanmak gerekiyor.

### Öneri
Benim log altyapımı genişlet: tüm Emare projelerinin loglarını tek yerde topla.

### Uygulama
```python
# Her projede: Emare Log'a log gönder
import logging
import requests

class EmareLogHandler(logging.Handler):
    def emit(self, record):
        requests.post("http://emare-log:8080/api/log", json={
            "project": "emare-finance",
            "level": record.levelname,
            "message": self.format(record),
            "timestamp": record.created
        })

# FastAPI projeler için:
logger = logging.getLogger("emare")
logger.addHandler(EmareLogHandler())
```

### Geliştirme Adımları
1. [ ] `/api/log` endpoint'i ekle (multi-project support)
2. [ ] SDK: `pip install emare-log-sdk`
3. [ ] Dashboard: proje bazlı filtre
4. [ ] Alert: error/critical gelince bildirim
5. [ ] Retention: 30 gün sakla, sil

### Beklenen Sonuç
21 proje tek log ekranından izlenir, sorun 10x daha hızlı tespit

---

## [4 Mart 2026] — AI ile Anomaly Detection

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare Log, SiberEmare

### Sorun
Loglar var ama analiz edilmiyor. Bir sunucu saldırı altında olsa bile saatlerce fark edilmiyor.

### Öneri
Gemini ile log analizi: normal pattern dışı davranışı tespit et.

```python
# Saatlik log özetini Gemini'ye gönder
prompt = f"""
Son 1 saatte {len(logs)} log girişi var.
Anormal davranış veya güvenlik tehlikesi var mı?

Log özeti:
{log_summary}
"""
response = gemini.generate_content(prompt)
if "tehlike" in response.text.lower() or "saldırı" in response.text.lower():
    send_whatsapp_alert(response.text)
```

### Geliştirme Adımları
1. [ ] Log aggregator: saatlik özet oluştur
2. [ ] Gemini API çağrısı: anomaly analizi
3. [ ] Bildirim: WhatsApp + dashboard uyarısı
4. [ ] Whitelist: bilinen pattern'lar için false positive azalt
5. [ ] SiberEmare ile entegrasyon: alert → otomatik port bloklama

### Beklenen Sonuç
Saldırılar gerçek zamanlı tespit, %0 manuel log okuma
