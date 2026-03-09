# {{PROJE_AD}} — Yardımcı Fonksiyonlar

from datetime import datetime


def now_str() -> str:
    """Şimdiki zamanı formatlanmış string olarak döndürür."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def slugify(text: str) -> str:
    """Metni URL-uyumlu slug'a çevirir."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")
