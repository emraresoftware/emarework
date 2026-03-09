#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          EMARE ÇEYİZ HAZIRLAMA SİSTEMİ                     ║
║          emarework Dervishi'nin Kutsal Görevi                ║
╚══════════════════════════════════════════════════════════════╝

Yeni bir Emare projesi için komple çeyiz hazırlar:
  - Proje klasör yapısı
  - Tüm temel dosyalar (README, requirements, config, vb.)
  - Ekosistem kimlik dosyaları (Anayasa, AI Collective, Ortak Hafıza...)
  - RBAC ağacı (DERVISHIN_CEYIZI.md)
  - web_dizayn/ (projeye özel renk paleti + landing page)
  - Makefile, .editorconfig, test dosyası
  - Derviş kaydı (EmareAPI) + Dergah bağlantısı
  - projects.json kaydı
  - EMARE_ORTAK_CALISMA bağlantısı

Kullanım:
  python3 ceyiz_hazirla.py                     # İnteraktif mod
  python3 ceyiz_hazirla.py --ad "emareX"       # Hızlı mod
  python3 ceyiz_hazirla.py --liste             # Şablon listesi

Şablon Tipleri:
  fastapi    — FastAPI + SQLAlchemy backend
  flask      — Flask web uygulaması
  react      — React + Next.js frontend
  cli        — Python CLI aracı
  fullstack  — FastAPI + React tam yığın
  library    — Python kütüphanesi
  bos        — Sadece iskelet (minimal)
"""

import json
import pathlib
import os
import sys
import shutil
import colorsys
from datetime import datetime

# ─── SABİTLER ───
ROOT = pathlib.Path("/Users/emre/Desktop/Emare")
EMAREAPI = ROOT / "emareapi"
DERVISLER = EMAREAPI / "Dervisler"
DERGAH = EMAREAPI / "Dergah"
PROJECTS_JSON = ROOT / "projects.json"
SABLONLAR_DIR = pathlib.Path(__file__).parent / "ceyiz_sablonlari"
ORTAK_CALISMA = ROOT / "EMARE_ORTAK_CALISMA"

# ─── RENK PALETİ (terminalde güzel çıksın) ───
class R:
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    END = "\033[0m"
    OK = f"{GREEN}✓{END}"
    FAIL = f"{RED}✗{END}"
    ARROW = f"{CYAN}→{END}"

def banner():
    print(f"""
{R.PURPLE}{R.BOLD}╔══════════════════════════════════════════════════════╗
║     🎁 EMARE ÇEYİZ HAZIRLAMA SİSTEMİ               ║
║     emarework Dervishi — v3.0                        ║
╚══════════════════════════════════════════════════════╝{R.END}
""")


# ═══════════════════════════════════════════
# RENK PALET ÜRETİCİ
# ═══════════════════════════════════════════

def hex_to_hsl(hex_color: str) -> tuple:
    """HEX -> HSL dönüşümü."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    h_, l, s = colorsys.rgb_to_hls(r, g, b)
    return h_ * 360, s * 100, l * 100


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """HSL -> HEX dönüşümü."""
    h_, s_, l_ = h / 360, s / 100, l / 100
    r, g, b = colorsys.hls_to_rgb(h_, l_, s_)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'


def renk_paleti_uret(ana_renk: str) -> dict:
    """
    Tek bir HEX renkten 50-950 arası 11 tonluk palet üretir.
    Tailwind CSS standardına uygun.
    """
    h, s, l = hex_to_hsl(ana_renk)
    # Lightness değerleri: 50=çok açık ... 950=çok koyu
    lightness_map = {
        '50': 97, '100': 94, '200': 86, '300': 74, '400': 62,
        '500': 50, '600': 42, '700': 34, '800': 26, '900': 18, '950': 10,
    }
    # Saturation ayarı: açık tonlarda biraz düşür, koyu tonlarda koru
    sat_map = {
        '50': max(s * 0.4, 20), '100': max(s * 0.5, 25), '200': max(s * 0.65, 35),
        '300': max(s * 0.8, 45), '400': max(s * 0.9, 55),
        '500': s, '600': s, '700': min(s * 1.05, 100),
        '800': min(s * 1.05, 100), '900': min(s * 1.0, 100), '950': min(s * 0.95, 100),
    }
    palet = {}
    for token, lig in lightness_map.items():
        sat = sat_map[token]
        palet[token] = hsl_to_hex(h, sat, lig)
    return palet


def proje_kisaltma_uret(ad: str) -> str:
    """Proje adından 2 harfli kısaltma üret (favicon için)."""
    parcalar = ad.replace('Emare', '').replace('emare', '').strip().split()
    if parcalar:
        if len(parcalar) >= 2:
            return (parcalar[0][0] + parcalar[1][0]).upper()
        return parcalar[0][:2].upper()
    return ad[:2].upper()


def web_dizayn_olustur(proje_yol: pathlib.Path, degiskenler: dict, ana_renk: str, sablon_tech: list):
    """
    web_dizayn/ klasörüne otomatik STYLE_NOTLARI.md + HTML landing page oluşturur.
    Projeye özel renk paletiyle.
    """
    wd = proje_yol / 'web_dizayn'
    wd.mkdir(parents=True, exist_ok=True)

    palet = renk_paleti_uret(ana_renk)
    kisaltma = proje_kisaltma_uret(degiskenler['PROJE_AD'])

    # Tech badge HTML üret
    badge_html = ''
    for tech in sablon_tech:
        badge_html += f'        <span class="px-4 py-2 rounded-full text-sm font-semibold" style="background:{palet["100"]};color:{palet["700"]}">{tech}</span>\n'

    # Renk değişkenlerini ekle
    renk_vars = {f'RENK_{k}': v for k, v in palet.items()}
    renk_vars['ANA_RENK'] = ana_renk
    renk_vars['PROJE_KISALTMA'] = kisaltma
    renk_vars['TECH_BADGES'] = badge_html
    tum_vars = {**degiskenler, **renk_vars}

    # STYLE_NOTLARI.md
    style_md = wd / 'STYLE_NOTLARI.md'
    if not style_md.exists():
        style_md.write_text(sablon_dosya_oku('style_notlari.md', tum_vars), encoding='utf-8')

    # HTML landing page
    proje_klasor = degiskenler.get('PROJE_KLASOR', 'emare')
    html_dosya = wd / f'{proje_klasor}_style.html'
    if not html_dosya.exists():
        html_dosya.write_text(sablon_dosya_oku('web_dizayn_html.html', tum_vars), encoding='utf-8')

    return palet

# ═══════════════════════════════════════════
# ŞABLON TANIMLARI
# ═══════════════════════════════════════════
SABLONLAR = {
    "fastapi": {
        "aciklama": "FastAPI + SQLAlchemy backend API",
        "icon": "⚡",
        "color": "#10b981",
        "tech": ["FastAPI", "Python", "SQLAlchemy", "SQLite", "Docker"],
        "category": "SaaS Platform",
        "dizinler": [
            "src/core", "src/api/v1", "src/api/middleware",
            "src/models", "src/services", "src/utils", "src/config",
            "templates", "static/css", "static/js", "static/img",
            "tests/unit", "tests/integration",
            "docs", "scripts", "data", "deploy",
        ],
        "dosyalar": {
            "main.py": "fastapi_main.py",
            "requirements.txt": "fastapi_requirements.txt",
            ".env.example": "env_example.txt",
            "Dockerfile": "dockerfile.txt",
            "docker-compose.yml": "docker_compose.txt",
            "src/__init__.py": "init_py.txt",
            "src/core/__init__.py": "init_py.txt",
            "src/core/app.py": "fastapi_app.py",
            "src/core/database.py": "fastapi_database.py",
            "src/config/__init__.py": "init_py.txt",
            "src/config/settings.py": "fastapi_settings.py",
            "src/models/__init__.py": "init_py.txt",
            "src/api/__init__.py": "init_py.txt",
            "src/api/v1/__init__.py": "init_py.txt",
            "src/api/v1/router.py": "fastapi_router.py",
            "src/api/middleware/__init__.py": "init_py.txt",
            "src/services/__init__.py": "init_py.txt",
            "src/utils/__init__.py": "init_py.txt",
            "src/utils/helpers.py": "utils_helpers.py",
            "tests/__init__.py": "init_py.txt",
            "tests/unit/__init__.py": "init_py.txt",
        },
    },
    "flask": {
        "aciklama": "Flask web uygulaması",
        "icon": "🌶️",
        "color": "#0ea5e9",
        "tech": ["Flask", "Python", "Jinja2", "SQLite", "Bootstrap 5"],
        "category": "Platform",
        "dizinler": [
            "templates", "static/css", "static/js", "static/img",
            "models", "routes", "services", "utils",
            "tests", "docs", "data",
        ],
        "dosyalar": {
            "app.py": "flask_app.py",
            "requirements.txt": "flask_requirements.txt",
            ".env.example": "env_example.txt",
            "models/__init__.py": "init_py.txt",
            "routes/__init__.py": "init_py.txt",
            "services/__init__.py": "init_py.txt",
            "utils/__init__.py": "init_py.txt",
            "tests/__init__.py": "init_py.txt",
        },
    },
    "react": {
        "aciklama": "React + Next.js frontend",
        "icon": "⚛️",
        "color": "#6366f1",
        "tech": ["React", "Next.js", "TypeScript", "Tailwind CSS"],
        "category": "Platform",
        "dizinler": [
            "public", "src/components", "src/pages", "src/styles",
            "src/hooks", "src/store", "src/utils", "src/lib",
            "tests",
        ],
        "dosyalar": {
            "package.json": "react_package.json",
            "next.config.js": "react_next_config.js",
            "tailwind.config.js": "react_tailwind_config.js",
            "tsconfig.json": "react_tsconfig.json",
            "src/pages/index.tsx": "react_index.tsx",
        },
    },
    "cli": {
        "aciklama": "Python CLI aracı",
        "icon": "🖥️",
        "color": "#f59e0b",
        "tech": ["Python", "Rich", "Click"],
        "category": "Tool",
        "dizinler": [
            "src", "tests", "docs",
        ],
        "dosyalar": {
            "main.py": "cli_main.py",
            "requirements.txt": "cli_requirements.txt",
            "src/__init__.py": "init_py.txt",
            "src/cli.py": "cli_cli.py",
            "tests/__init__.py": "init_py.txt",
        },
    },
    "fullstack": {
        "aciklama": "FastAPI + React tam yığın uygulama",
        "icon": "🚀",
        "color": "#8b5cf6",
        "tech": ["FastAPI", "Python", "React", "Next.js", "PostgreSQL", "Redis", "Docker"],
        "category": "Platform",
        "dizinler": [
            "backend/src/core", "backend/src/api/v1", "backend/src/api/middleware",
            "backend/src/models", "backend/src/services", "backend/src/utils",
            "backend/src/config", "backend/tests",
            "frontend/public", "frontend/src/components", "frontend/src/pages",
            "frontend/src/styles", "frontend/src/hooks", "frontend/src/store",
            "frontend/src/utils",
            "mobile/ios", "mobile/android", "mobile/shared",
            "docs/api", "docs/architecture",
            "deploy", "scripts", "data",
        ],
        "dosyalar": {
            "docker-compose.yml": "fullstack_docker_compose.txt",
            "backend/main.py": "fastapi_main.py",
            "backend/requirements.txt": "fastapi_requirements.txt",
            "backend/src/__init__.py": "init_py.txt",
            "backend/src/core/__init__.py": "init_py.txt",
            "backend/src/core/app.py": "fastapi_app.py",
            "backend/src/config/__init__.py": "init_py.txt",
            "backend/src/config/settings.py": "fastapi_settings.py",
            "backend/src/models/__init__.py": "init_py.txt",
            "backend/src/api/__init__.py": "init_py.txt",
            "backend/src/api/v1/__init__.py": "init_py.txt",
            "backend/src/api/v1/router.py": "fastapi_router.py",
            "backend/src/services/__init__.py": "init_py.txt",
            "backend/src/utils/__init__.py": "init_py.txt",
            "backend/tests/__init__.py": "init_py.txt",
            "frontend/package.json": "react_package.json",
        },
    },
    "library": {
        "aciklama": "Python kütüphanesi / paket",
        "icon": "📦",
        "color": "#ec4899",
        "tech": ["Python", "pytest"],
        "category": "Tool",
        "dizinler": [
            "src", "tests", "docs", "examples",
        ],
        "dosyalar": {
            "pyproject.toml": "lib_pyproject.toml",
            "requirements.txt": "lib_requirements.txt",
            "src/__init__.py": "lib_init.py",
            "tests/__init__.py": "init_py.txt",
            "tests/test_main.py": "lib_test_main.py",
        },
    },
    "bos": {
        "aciklama": "Minimal iskelet — sadece temel yapı",
        "icon": "📄",
        "color": "#64748b",
        "tech": ["Python"],
        "category": "Tool",
        "dizinler": [
            "src", "docs", "tests",
        ],
        "dosyalar": {
            "main.py": "bos_main.py",
        },
    },
}


# ═══════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════

def load_projects():
    """projects.json oku."""
    return json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))


def save_projects(projects):
    """projects.json yaz."""
    PROJECTS_JSON.write_text(
        json.dumps(projects, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def sablon_dosya_oku(sablon_adi: str, degiskenler: dict) -> str:
    """Şablon dosyasını oku ve değişkenleri yerleştir."""
    sablon_yol = SABLONLAR_DIR / sablon_adi
    if not sablon_yol.exists():
        return f"# {degiskenler.get('PROJE_AD', 'Emare Proje')}\n# TODO: İçerik eklenecek\n"
    icerik = sablon_yol.read_text(encoding="utf-8")
    for key, val in degiskenler.items():
        icerik = icerik.replace(f"{{{{{key}}}}}", str(val))
    return icerik


def interaktif_bilgi_topla() -> dict:
    """Kullanıcıdan proje bilgilerini topla."""
    print(f"\n{R.BOLD}📋 Proje Bilgileri{R.END}\n")

    # Ad
    while True:
        ad = input(f"  {R.ARROW} Proje adı (klasör adı, ör: emareX): ").strip()
        if ad:
            break
        print(f"  {R.FAIL} Boş olamaz!")

    # Görünen ad
    varsayilan_gorunen = ad.replace("emare", "Emare ").replace("  ", " ").strip()
    gorunen_ad = input(f"  {R.ARROW} Görünen ad [{varsayilan_gorunen}]: ").strip()
    if not gorunen_ad:
        gorunen_ad = varsayilan_gorunen

    # Açıklama
    aciklama = input(f"  {R.ARROW} Açıklama: ").strip()
    if not aciklama:
        aciklama = f"{gorunen_ad} — Emare ekosistemi projesi"

    # Şablon seçimi
    print(f"\n{R.BOLD}📐 Şablon Tipleri:{R.END}")
    sablon_listesi = list(SABLONLAR.keys())
    for i, (key, val) in enumerate(SABLONLAR.items(), 1):
        print(f"  {R.CYAN}{i}{R.END}. {val['icon']} {key:12s} — {val['aciklama']}")

    while True:
        secim = input(f"\n  {R.ARROW} Şablon numarası [1]: ").strip()
        if not secim:
            secim = "1"
        try:
            idx = int(secim) - 1
            if 0 <= idx < len(sablon_listesi):
                sablon = sablon_listesi[idx]
                break
        except ValueError:
            if secim in SABLONLAR:
                sablon = secim
                break
        print(f"  {R.FAIL} Geçersiz seçim!")

    # Kategori
    print(f"\n{R.BOLD}📂 Kategoriler:{R.END}")
    kategoriler = ["SaaS Platform", "Platform", "Tool", "Infrastructure", "Security", "Core Engine", "Automation", "POS"]
    for i, k in enumerate(kategoriler, 1):
        print(f"  {R.CYAN}{i}{R.END}. {k}")
    kat_secim = input(f"\n  {R.ARROW} Kategori numarası [{kategoriler.index(SABLONLAR[sablon]['category'])+1}]: ").strip()
    if kat_secim:
        try:
            kategori = kategoriler[int(kat_secim) - 1]
        except (ValueError, IndexError):
            kategori = SABLONLAR[sablon]["category"]
    else:
        kategori = SABLONLAR[sablon]["category"]

    # Port
    port_str = input(f"  {R.ARROW} Port (boş = yok): ").strip()
    port = int(port_str) if port_str.isdigit() else None

    return {
        "ad": ad,
        "gorunen_ad": gorunen_ad,
        "aciklama": aciklama,
        "sablon": sablon,
        "kategori": kategori,
        "port": port,
    }


# ═══════════════════════════════════════════
# ANA ÇEYİZ FONKSİYONU
# ═══════════════════════════════════════════

def ceyiz_hazirla(bilgi: dict) -> dict:
    """
    Tam çeyiz hazırla — proje klasörü + derviş + kayıt.
    Döndürür: {"basarili": bool, "detay": {...}}
    """
    ad = bilgi["ad"]
    gorunen_ad = bilgi["gorunen_ad"]
    aciklama = bilgi["aciklama"]
    sablon_key = bilgi["sablon"]
    kategori = bilgi["kategori"]
    port = bilgi.get("port")

    sablon = SABLONLAR[sablon_key]
    proje_yol = ROOT / ad

    sonuc = {
        "ad": ad,
        "yol": str(proje_yol),
        "adimlar": [],
    }

    def adim(mesaj, durum="ok"):
        sonuc["adimlar"].append({"mesaj": mesaj, "durum": durum})
        icon = R.OK if durum == "ok" else R.FAIL
        print(f"  {icon} {mesaj}")

    print(f"\n{R.BOLD}🎁 Çeyiz hazırlanıyor: {R.CYAN}{gorunen_ad}{R.END}\n")

    # ── 1. Proje klasörü var mı kontrol ──
    if proje_yol.exists():
        adim(f"Klasör zaten mevcut: {ad} — üzerine ekleniyor", "ok")
    else:
        proje_yol.mkdir(parents=True)
        adim(f"Proje klasörü oluşturuldu: {ad}")

    # ── 2. Alt dizinler ──
    for dizin in sablon["dizinler"]:
        (proje_yol / dizin).mkdir(parents=True, exist_ok=True)
    adim(f"{len(sablon['dizinler'])} alt dizin oluşturuldu")

    # Ortak dizinler (her projede olmalı)
    for ortak in ["web_dizayn", "EMARE_ORTAK_CALISMA"]:
        d = proje_yol / ortak
        if ortak == "EMARE_ORTAK_CALISMA":
            if not d.exists() and not d.is_symlink():
                d.symlink_to(ORTAK_CALISMA)
                adim("EMARE_ORTAK_CALISMA symlink bağlandı")
        else:
            d.mkdir(parents=True, exist_ok=True)

    # ── 3. Şablon değişkenleri ──
    degiskenler = {
        "PROJE_AD": gorunen_ad,
        "PROJE_KLASOR": ad,
        "PROJE_ACIKLAMA": aciklama,
        "PROJE_YOL": str(proje_yol),
        "PROJE_PORT": str(port or 8000),
        "PROJE_KATEGORI": kategori,
        "PROJE_TARIH": datetime.now().strftime("%d %B %Y"),
        "PROJE_TECH": ", ".join(sablon["tech"]),
        "PROJE_ICON": sablon["icon"],
    }

    # ── 4. Şablon dosyaları ──
    dosya_sayisi = 0
    for hedef, sablon_dosya in sablon["dosyalar"].items():
        hedef_yol = proje_yol / hedef
        hedef_yol.parent.mkdir(parents=True, exist_ok=True)
        if not hedef_yol.exists():
            icerik = sablon_dosya_oku(sablon_dosya, degiskenler)
            hedef_yol.write_text(icerik, encoding="utf-8")
            dosya_sayisi += 1
    adim(f"{dosya_sayisi} şablon dosyası oluşturuldu")

    # ── 5. README.md ──
    readme = proje_yol / "README.md"
    if not readme.exists():
        readme.write_text(sablon_dosya_oku("readme.md", degiskenler), encoding="utf-8")
        adim("README.md oluşturuldu")

    # ── 6. DOSYA_YAPISI.md ──
    dosya_yapisi = proje_yol / "DOSYA_YAPISI.md"
    if not dosya_yapisi.exists():
        # Otomatik ağaç oluştur
        lines = [f"# {gorunen_ad} — Dosya Yapısı\n", "```"]
        for dizin in sorted(sablon["dizinler"]):
            lines.append(f"├── {dizin}/")
        for dosya in sorted(sablon["dosyalar"].keys()):
            lines.append(f"├── {dosya}")
        lines.extend([
            "├── DERVISHIN_CEYIZI.md",
            "├── EMARE_ANAYASA.md",
            "├── EMARE_AI_COLLECTIVE.md",
            "├── EMARE_ORTAK_HAFIZA.md",
            "├── COPILOT_SESSION_HAFIZA.md",
            "├── QUICKSTART_DEV.md",
            "├── CONTRIBUTING.md",
            "├── CHANGELOG.md",
            "├── Makefile",
            "├── .editorconfig",
            "├── README.md",
            "├── DOSYA_YAPISI.md",
            "├── tests/",
            "│   └── test_ceyiz.py",
            "├── web_dizayn/",
            "│   ├── STYLE_NOTLARI.md",
            "│   └── {}_style.html".format(ad),
            "└── EMARE_ORTAK_CALISMA/",
            "```",
        ])
        dosya_yapisi.write_text("\n".join(lines), encoding="utf-8")
        adim("DOSYA_YAPISI.md oluşturuldu")

    # ── 7. .gitignore ──
    gitignore = proje_yol / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            ".venv/\n__pycache__/\n*.pyc\n.env\ndata/*.db\nnode_modules/\n"
            ".DS_Store\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/\n.coverage\n",
            encoding="utf-8",
        )
        adim(".gitignore oluşturuldu")

    # ── 8. Hafıza dosyası ──
    hafiza = proje_yol / f"{ad.upper()}_HAFIZA.md"
    if not hafiza.exists():
        hafiza.write_text(
            f"# {gorunen_ad} — Proje Hafıza Dosyası\n\n"
            f"## Proje Bilgileri\n"
            f"- **Ad**: {gorunen_ad}\n"
            f"- **ID**: {ad}\n"
            f"- **Kategori**: {kategori}\n"
            f"- **Durum**: Development\n"
            f"- **Port**: {port or 'Yok'}\n\n"
            f"## Kronoloji\n"
            f"- **{degiskenler['PROJE_TARIH']}**: Çeyiz hazırlandı (emarework Dervishi)\n"
            f"  - Şablon: {sablon_key}\n"
            f"  - Teknoloji: {', '.join(sablon['tech'])}\n",
            encoding="utf-8",
        )
        adim("Hafıza dosyası oluşturuldu")

    # ── 9. EKOSİSTEM KİMLİK DOSYALARI ──
    ekosistem_dosyalari = {
        "EMARE_ANAYASA.md": "emare_anayasa.md",
        "EMARE_AI_COLLECTIVE.md": "emare_ai_collective.md",
        "EMARE_ORTAK_HAFIZA.md": "emare_ortak_hafiza.md",
        "COPILOT_SESSION_HAFIZA.md": "copilot_session_hafiza.md",
        "QUICKSTART_DEV.md": "quickstart_dev.md",
        "CONTRIBUTING.md": "contributing.md",
        "CHANGELOG.md": "changelog.md",
    }
    eko_sayisi = 0
    for hedef_ad, sablon_ad in ekosistem_dosyalari.items():
        hedef = proje_yol / hedef_ad
        if not hedef.exists():
            hedef.write_text(sablon_dosya_oku(sablon_ad, degiskenler), encoding="utf-8")
            eko_sayisi += 1
    adim(f"{eko_sayisi} ekosistem kimlik dosyası oluşturuldu (Anayasa, AI Collective, Ortak Hafıza...)")

    # ── 10. Makefile + .editorconfig ──
    makefile = proje_yol / "Makefile"
    if not makefile.exists():
        makefile.write_text(sablon_dosya_oku("makefile.txt", degiskenler), encoding="utf-8")
    editorconfig = proje_yol / ".editorconfig"
    if not editorconfig.exists():
        editorconfig.write_text(sablon_dosya_oku("editorconfig.txt", degiskenler), encoding="utf-8")
    adim("Makefile + .editorconfig oluşturuldu")

    # ── 11. Test dosyası (temel çeyiz testleri) ──
    test_dir = proje_yol / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_ceyiz = test_dir / "test_ceyiz.py"
    if not test_ceyiz.exists():
        test_ceyiz.write_text(sablon_dosya_oku("test_ceyiz.py", degiskenler), encoding="utf-8")
        adim("tests/test_ceyiz.py oluşturuldu (çeyiz doğrulama testleri)")

    # ── 12. DERVİŞİN ÇEYİZİ (olmazsa olmaz — RBAC ağacı) ──
    ceyiz_dosya = proje_yol / "DERVISHIN_CEYIZI.md"
    if not ceyiz_dosya.exists():
        ceyiz_dosya.write_text(sablon_dosya_oku("dervishin_ceyizi.md", degiskenler), encoding="utf-8")
        adim("DERVISHIN_CEYIZI.md oluşturuldu (RBAC ağacı)")

    # ── 13. web_dizayn/ otomatik doldurma ──
    palet = web_dizayn_olustur(proje_yol, degiskenler, sablon["color"], sablon["tech"])
    adim(f"web_dizayn/ oluşturuldu (renk: {sablon['color']} → 11 ton palet)")

    # ── 14. setup.sh + start.sh ──
    setup_sh = proje_yol / "setup.sh"
    if not setup_sh.exists():
        setup_sh.write_text(sablon_dosya_oku("setup_sh.txt", degiskenler), encoding="utf-8")
        setup_sh.chmod(0o755)
    start_sh = proje_yol / "start.sh"
    if not start_sh.exists():
        start_sh.write_text(sablon_dosya_oku("start_sh.txt", degiskenler), encoding="utf-8")
        start_sh.chmod(0o755)
    adim("setup.sh + start.sh oluşturuldu")

    # ═══ 15. DERVİŞ KAYDI ═══
    dervish_ad = f"{ad} Dervishi"
    dervish_yol = DERVISLER / dervish_ad
    dervish_yol.mkdir(parents=True, exist_ok=True)

    # DERVISH_PROFIL.md
    (dervish_yol / "DERVISH_PROFIL.md").write_text(
        f"# {dervish_ad}\n\n"
        f"- Sorumlu Klasör Sahibi: {ad}\n"
        f"- Proje Yolu: {proje_yol}\n"
        f"- Şablon: {sablon_key}\n"
        f"- Kategori: {kategori}\n"
        f"- Çeyiz Tarihi: {degiskenler['PROJE_TARIH']}\n\n"
        f"## Görev\n"
        f"- {gorunen_ad} projesinden birincil sorumludur.\n"
        f"- Dergah üzerinden diğer Dervişlere öneri sunar.\n\n"
        f"## Teknoloji\n"
        + "".join(f"- {t}\n" for t in sablon["tech"]),
        encoding="utf-8",
    )

    # PROJE_KISAYOLU symlink
    link = dervish_yol / "PROJE_KISAYOLU"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(proje_yol)

    # Dergah symlink
    dlink = DERGAH / dervish_ad
    if dlink.exists() or dlink.is_symlink():
        dlink.unlink()
    dlink.symlink_to(pathlib.Path("..") / "Dervisler" / dervish_ad)

    # emareapi Dervishi.md güncelle
    master_md = EMAREAPI / "emareapi Dervishi.md"
    if master_md.exists():
        content = master_md.read_text(encoding="utf-8")
        if ad not in content:
            content = content.rstrip() + f"\n- {dervish_ad} -> {proje_yol}\n"
            master_md.write_text(content, encoding="utf-8")

    # DERVISH_YETENEKLER.json (koordinasyon sistemi için)
    yetenek_dosya = dervish_yol / "DERVISH_YETENEKLER.json"
    if not yetenek_dosya.exists():
        yetenek_dosya.write_text(
            sablon_dosya_oku("dervish_yetenekler.json", degiskenler),
            encoding="utf-8",
        )

    # gorev_kutusu/ klasörleri (Dervişler arası iletişim)
    for kutu in ("gelen", "giden", "tamamlanan"):
        (dervish_yol / "gorev_kutusu" / kutu).mkdir(parents=True, exist_ok=True)

    adim(f"Derviş kaydı yapıldı: {dervish_ad} (+ yetenek + görev kutusu)")
    adim("Dergah bağlantısı kuruldu")

    # ═══ 16. PROJECTS.JSON KAYDI ═══
    projects = load_projects()
    mevcut_ids = {p["id"] for p in projects}
    proje_id = ad.lower().replace(" ", "-")

    if proje_id not in mevcut_ids:
        yeni_kayit = {
            "id": proje_id,
            "name": gorunen_ad,
            "icon": sablon["icon"],
            "color": sablon["color"],
            "description": aciklama,
            "status": "development",
            "tech": sablon["tech"],
            "path": str(proje_yol),
            "memory_file": str(hafiza) if hafiza.exists() else None,
            "server": None,
            "local_start_cmd": "python3 main.py" if sablon_key != "react" else "npm run dev",
            "local_port": port,
            "category": kategori,
            "url": None,
            "notes": [],
        }
        projects.append(yeni_kayit)
        save_projects(projects)
        adim(f"projects.json kaydı yapıldı (toplam: {len(projects)} proje)")
    else:
        adim(f"projects.json'da zaten kayıtlı: {proje_id}", "ok")

    # ═══ SONUÇ ═══
    sonuc["basarili"] = True
    dosya_say = sum(1 for _ in proje_yol.rglob("*") if _.is_file())
    dizin_say = sum(1 for _ in proje_yol.rglob("*") if _.is_dir())

    print(f"\n{R.GREEN}{R.BOLD}═══════════════════════════════════════════{R.END}")
    print(f"  {R.GREEN}🎉 Çeyiz hazır!{R.END}")
    print(f"  {R.ARROW} Proje: {R.BOLD}{gorunen_ad}{R.END}")
    print(f"  {R.ARROW} Yol: {proje_yol}")
    print(f"  {R.ARROW} Şablon: {sablon_key}")
    print(f"  {R.ARROW} Dosya: {dosya_say} | Dizin: {dizin_say}")
    print(f"  {R.ARROW} Derviş: {dervish_ad}")
    print(f"  {R.ARROW} Port: {port or 'Yok'}")
    print(f"{R.GREEN}{R.BOLD}═══════════════════════════════════════════{R.END}\n")

    return sonuc


def sablon_listesi_goster():
    """Mevcut şablonları listele."""
    print(f"\n{R.BOLD}📐 Kullanılabilir Çeyiz Şablonları:{R.END}\n")
    for key, val in SABLONLAR.items():
        print(f"  {val['icon']} {R.BOLD}{key:12s}{R.END} — {val['aciklama']}")
        print(f"    {R.BLUE}Tech:{R.END} {', '.join(val['tech'])}")
        print(f"    {R.BLUE}Dirs:{R.END} {len(val['dizinler'])} dizin | {len(val['dosyalar'])} dosya")
        print()


# ═══════════════════════════════════════════
# CLI GİRİŞ NOKTASI
# ═══════════════════════════════════════════

def main():
    banner()

    # Argüman ayrıştırma
    args = sys.argv[1:]

    if "--liste" in args or "--list" in args:
        sablon_listesi_goster()
        return

    if "--ad" in args:
        idx = args.index("--ad")
        ad = args[idx + 1] if idx + 1 < len(args) else None
        if not ad:
            print(f"{R.FAIL} --ad parametresi boş!")
            return

        sablon = "fastapi"
        if "--sablon" in args:
            s_idx = args.index("--sablon")
            sablon = args[s_idx + 1] if s_idx + 1 < len(args) else "fastapi"

        aciklama = ""
        if "--aciklama" in args:
            a_idx = args.index("--aciklama")
            aciklama = args[a_idx + 1] if a_idx + 1 < len(args) else ""

        port = None
        if "--port" in args:
            p_idx = args.index("--port")
            try:
                port = int(args[p_idx + 1])
            except (ValueError, IndexError):
                port = None

        gorunen = ad.replace("emare", "Emare ").replace("  ", " ").strip()
        if not aciklama:
            aciklama = f"{gorunen} — Emare ekosistemi projesi"

        bilgi = {
            "ad": ad,
            "gorunen_ad": gorunen,
            "aciklama": aciklama,
            "sablon": sablon,
            "kategori": SABLONLAR.get(sablon, SABLONLAR["bos"])["category"],
            "port": port,
        }
        ceyiz_hazirla(bilgi)
    else:
        # İnteraktif mod
        bilgi = interaktif_bilgi_topla()
        ceyiz_hazirla(bilgi)


if __name__ == "__main__":
    main()
