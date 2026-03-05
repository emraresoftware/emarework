# 🤖 AI-KATIP — Yazılım Geliştirme Önerileri

> **Proje:** Emare Katip — AI Sekreterlik & Asistan  
> **Uzmanlık:** Doğal Dil İşleme + Takvim + E-posta + Otomasyon  
> **Son Güncelleme:** 4 Mart 2026

---

## [4 Mart 2026] — Emare Asistan ile Sinerji: Ortak NLP Altyapısı

**Öncelik:** 🟠 Yüksek  
**Kapsam:** Emare Katip, Emare Asistan

### Sorun
İki AI asistan projesi paralel gidiyor (Emare Asistan ve Emare Katip). Her ikisi de NLP, intent detection, entity extraction yapıyor. Kod duplicasyonu var.

### Öneri
Ortak bir **Emare NLP Engine** oluştur. Her iki proje bu ortak motoru kullansın.

```python
# Ortak engine
nlp = EmareNLP()
result = nlp.parse("3 Mart'a toplantı ekle saat 15:00")
# → {intent: "calendar_add", date: "2026-03-03", time: "15:00"}

result = nlp.parse("Faturamı bugün gönder")
# → {intent: "invoice_send", target: "today"}
```

### Geliştirme Adımları
1. [ ] Emare Asistan + Katip'in ortak intent'lerini belirle
2. [ ] Shared entity extractor (tarih, saat, isim, miktar…)
3. [ ] Ortak intent model eğitimi (Gemini fine-tune)
4. [ ] `pip install emare-nlp` olarak paketle
5. [ ] Her iki proje de bu paketi import eder

### Beklenen Sonuç
%50 kod azalması, NLP kalitesi artar (daha fazla veriyle eğitim)

---

## [4 Mart 2026] — Toplantı Özeti & Karar Takibi

**Öncelik:** 🟡 Orta  
**Kapsam:** Emare Katip, Emare Team

### Sorun
Toplantılar oluyor ama kararlar yazılmıyor. Sonraki toplantıda "ne karar vermiştik?" sorusu.

### Öneri
Toplantı kaydı → AI özeti → karar listesi → Emare Team'e görev oluştur.

### Akış
```
Zoom/Meet kayıt → Whisper (transkript) 
→ Gemini (özet + kararlar) 
→ Emare Team (otomatik görev oluştur)
→ Emare Katip (hatırlatıcı kur)
```

### Geliştirme Adımları
1. [ ] Whisper entegrasyonu (ses → metin)
2. [ ] Karar çıkarma prompt'u: "Bu toplantıda ne karar verildi?"
3. [ ] Emare Team API: otomatik görev oluştur
4. [ ] 1 hafta sonra hatırlatıcı: "Geçen toplantıda X kararı alındı, durum ne?"
5. [ ] Katılımcılara özet e-posta

### Beklenen Sonuç
Hiçbir toplantı kararı unutulmaz, eylem izi tam
