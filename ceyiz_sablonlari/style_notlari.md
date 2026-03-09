# {{PROJE_AD}} — Tasarım Rehberi (Design System)

> Otomatik oluşturuldu: emarework Dervishi — Çeyiz Sistemi
> Ana Renk: `{{ANA_RENK}}`
> Tarih: {{PROJE_TARIH}}

---

## 1. RENK PALETİ (Brand Colors)

| Token | HEX | Kullanım |
|-------|-----|----------|
| `brand-50` | `{{RENK_50}}` | Çok açık arka plan, hover bg |
| `brand-100` | `{{RENK_100}}` | Açık arka plan |
| `brand-200` | `{{RENK_200}}` | Border (secondary buton) |
| `brand-300` | `{{RENK_300}}` | İkon accent |
| `brand-400` | `{{RENK_400}}` | Hover accent |
| `brand-500` | `{{RENK_500}}` | **Ana marka rengi (Primary)** |
| `brand-600` | `{{RENK_600}}` | Hover/active primary |
| `brand-700` | `{{RENK_700}}` | Koyu primary |
| `brand-800` | `{{RENK_800}}` | Koyu bg accent |
| `brand-900` | `{{RENK_900}}` | Çok koyu bg |
| `brand-950` | `{{RENK_950}}` | En koyu bg (hero, footer) |

---

## 2. GRİ TONLARI

| Token | Kullanım |
|-------|----------|
| `white` | Sayfa arka planı, kart arka planı |
| `gray-100` | Border, divider |
| `gray-300` | Footer body text |
| `gray-500` | Kart açıklamaları |
| `gray-600` | Body paragraph text |
| `gray-800` | Varsayılan metin |
| `gray-900` | Başlıklar |
| `gray-950` | Footer arka plan |

---

## 3. EK RENKLER

| Renk | HEX | Kullanım |
|------|-----|----------|
| Success | `#22c55e` | Başarı, onay |
| Warning | `#f59e0b` | Uyarı |
| Error | `#ef4444` | Hata |
| Info | `#3b82f6` | Bilgi |

---

## 4. GRADYANLAR

### Primary Buton
```css
background: linear-gradient(to right, {{RENK_500}}, {{RENK_700}});
```

### Gradient Text
```css
background: linear-gradient(135deg, {{RENK_600}}, {{RENK_400}});
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

### Hero Koyu Arka Plan
```css
background: linear-gradient(-45deg, {{RENK_950}}, {{RENK_900}}, {{RENK_800}});
```

---

## 5. TİPOGRAFİ

| Element | Font | Size | Weight |
|---------|------|------|--------|
| H1 | Inter | 3rem (48px) | 800 (ExtraBold) |
| H2 | Inter | 2.25rem (36px) | 700 (Bold) |
| H3 | Inter | 1.5rem (24px) | 600 (SemiBold) |
| Body | Inter | 1rem (16px) | 400 (Regular) |
| Small | Inter | 0.875rem (14px) | 400 |
| Button | Inter | 0.875rem (14px) | 600 |

---

## 6. SPACING

| Token | Değer | Kullanım |
|-------|-------|----------|
| xs | 4px | İkon-metin arası |
| sm | 8px | Küçük aralık |
| md | 16px | Kart padding |
| lg | 24px | Bölüm arası |
| xl | 48px | Büyük bölüm arası |
| 2xl | 96px | Hero section padding |

---

## 7. TAILWIND CONFIG

```javascript
tailwind.config = {
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: {
        brand: {
          50: '{{RENK_50}}',
          100: '{{RENK_100}}',
          200: '{{RENK_200}}',
          300: '{{RENK_300}}',
          400: '{{RENK_400}}',
          500: '{{RENK_500}}',
          600: '{{RENK_600}}',
          700: '{{RENK_700}}',
          800: '{{RENK_800}}',
          900: '{{RENK_900}}',
          950: '{{RENK_950}}',
        }
      }
    }
  }
}
```

---

*Otomatik oluşturuldu — emarework Dervishi Çeyiz Sistemi*
