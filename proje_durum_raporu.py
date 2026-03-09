#!/usr/bin/env python3
"""
Emare Ekosistemi — Proje Durum Raporu & Otomatik Tarayıcı
=========================================================
43 projeyi Git, dosya yapısı, port erişimi ve içerik bazında tarar.
projects.json'a `phase`, `completion_percent`, `last_active`, 
`commit_count`, `file_count`, `health_score` alanlarını ekler.

Kullanım:
    python proje_durum_raporu.py              # Tarama + rapor
    python proje_durum_raporu.py --guncelle   # projects.json'u günceller
    python proje_durum_raporu.py --json       # JSON çıktı verir
"""

import json
import os
import subprocess
import sys
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Sabitler ───────────────────────────────────────────────
EMARE_ROOT = Path("/Users/emre/Desktop/Emare")
PROJECTS_JSON = EMARE_ROOT / "projects.json"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".cache", ".mypy_cache", ".pytest_cache", "vendor", "storage"}

# Faz belirleme eşikleri
PHASE_THRESHOLDS = {
    # (min_dosya, min_commit, min_code_dosya) → faz
    "production": {"min_files": 15, "min_commits": 2, "has_server": True},
    "beta":       {"min_files": 500, "min_commits": 5},
    "alpha":      {"min_files": 100, "min_commits": 3},
    "mvp":        {"min_files": 30,  "min_commits": 2},
    "scaffold":   {"min_files": 5,   "min_commits": 1},
    "idea":       {"min_files": 0,   "min_commits": 0},
}

# Kod dosyası uzantıları
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".php", ".c", ".h", ".rs",
    ".go", ".java", ".rb", ".vue", ".svelte", ".css", ".scss",
    ".html", ".sql", ".sh", ".yml", ".yaml", ".toml"
}


# ─── Yardımcı Fonksiyonlar ─────────────────────────────────

def dosya_say(path: str) -> dict:
    """Klasördeki dosya istatistiklerini hesapla."""
    sonuc = {"toplam": 0, "kod": 0, "test": 0, "doc": 0, "config": 0}
    if not os.path.isdir(path):
        return sonuc
    
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            sonuc["toplam"] += 1
            ext = os.path.splitext(f)[1].lower()
            
            if ext in CODE_EXTENSIONS:
                sonuc["kod"] += 1
            if "test" in f.lower() or "spec" in f.lower():
                sonuc["test"] += 1
            if ext in {".md", ".txt", ".rst", ".pdf"}:
                sonuc["doc"] += 1
            if f in {"requirements.txt", "package.json", "composer.json", "Cargo.toml",
                     "pyproject.toml", "Makefile", "Dockerfile", "docker-compose.yml",
                     ".env", ".env.example", "setup.py", "setup.cfg"}:
                sonuc["config"] += 1
    
    return sonuc


def git_bilgisi(path: str) -> dict:
    """Git repo bilgilerini çek."""
    sonuc = {
        "commit_sayisi": 0,
        "son_commit_tarih": None,
        "son_commit_mesaj": None,
        "branch": None,
        "ilk_commit_tarih": None,
        "aktif_gun": 0,
    }
    
    if not os.path.isdir(os.path.join(path, ".git")):
        return sonuc
    
    try:
        # Commit sayısı
        r = subprocess.run(["git", "rev-list", "--count", "HEAD"],
                          capture_output=True, text=True, cwd=path, timeout=5)
        if r.returncode == 0:
            sonuc["commit_sayisi"] = int(r.stdout.strip())
        
        # Son commit
        r = subprocess.run(["git", "log", "-1", "--format=%ci|||%s"],
                          capture_output=True, text=True, cwd=path, timeout=5)
        if r.returncode == 0:
            parts = r.stdout.strip().split("|||")
            sonuc["son_commit_tarih"] = parts[0][:19] if parts[0] else None
            sonuc["son_commit_mesaj"] = parts[1] if len(parts) > 1 else None
        
        # İlk commit
        r = subprocess.run(["git", "log", "--reverse", "--format=%ci", "-1"],
                          capture_output=True, text=True, cwd=path, timeout=5)
        if r.returncode == 0:
            sonuc["ilk_commit_tarih"] = r.stdout.strip()[:19]
        
        # Aktif branch
        r = subprocess.run(["git", "branch", "--show-current"],
                          capture_output=True, text=True, cwd=path, timeout=5)
        if r.returncode == 0:
            sonuc["branch"] = r.stdout.strip()
        
        # Benzersiz aktif gün sayısı
        r = subprocess.run(["git", "log", "--format=%cd", "--date=short"],
                          capture_output=True, text=True, cwd=path, timeout=5)
        if r.returncode == 0:
            gun_listesi = set(r.stdout.strip().split("\n"))
            sonuc["aktif_gun"] = len([g for g in gun_listesi if g])
            
    except (subprocess.TimeoutExpired, Exception):
        pass
    
    return sonuc


def port_kontrol(port: Optional[int], host: str = "127.0.0.1") -> bool:
    """Port'un açık olup olmadığını kontrol et."""
    if not port:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except:
        return False


def onemli_dosya_kontrol(path: str) -> dict:
    """Proje sağlığını belirleyen kritik dosyaları kontrol et."""
    kontroller = {
        "readme": False,
        "requirements": False,
        "dockerfile": False,
        "tests": False,
        "ci_cd": False,
        "env_config": False,
        "hafiza": False,
        "anayasa": False,
    }
    
    if not os.path.isdir(path):
        return kontroller
    
    for item in os.listdir(path):
        lower = item.lower()
        if lower.startswith("readme"):
            kontroller["readme"] = True
        if lower in ("requirements.txt", "package.json", "composer.json", "cargo.toml", "pyproject.toml"):
            kontroller["requirements"] = True
        if lower in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
            kontroller["dockerfile"] = True
        if lower in (".env", ".env.example", "env.example"):
            kontroller["env_config"] = True
        if lower.endswith("_hafiza.md") or "hafıza" in lower or "hafiza" in lower:
            kontroller["hafiza"] = True
    
    # Tests klasörü
    if os.path.isdir(os.path.join(path, "tests")) or os.path.isdir(os.path.join(path, "test")):
        kontroller["tests"] = True
    
    # CI/CD
    if os.path.isdir(os.path.join(path, ".github")):
        kontroller["ci_cd"] = True
    
    # Anayasa/Ortak çalışma
    if os.path.isdir(os.path.join(path, "EMARE_ORTAK_CALISMA")):
        kontroller["anayasa"] = True
    
    return kontroller


def faz_belirle(proje: dict, dosyalar: dict, git: dict, dosya_kontrol: dict, port_acik: bool) -> tuple:
    """Projenin geliştirme fazını ve tamamlanma yüzdesini hesapla."""
    status = proje.get("status", "")
    toplam = dosyalar["toplam"]
    kod = dosyalar["kod"]
    commits = git["commit_sayisi"]
    
    # Üretimde olan ve sunucusu olan projeler
    if status == "production":
        # Production'da olsa bile gerçekten kapsamlı mı?
        if toplam > 1000:
            return "production", 90
        elif toplam > 100:
            return "production", 80
        else:
            return "production", 70
    
    if status == "ready":
        if toplam > 100:
            return "beta", 75
        else:
            return "beta", 65
    
    # Development projeler — en karmaşık hesaplama
    if toplam > 2000 and commits > 5:
        phase = "alpha"
        pct = min(60, 30 + (toplam // 200))
    elif toplam > 500 and commits > 3:
        phase = "alpha"
        pct = min(50, 25 + (toplam // 200))
    elif toplam > 100 and commits > 2:
        phase = "mvp"
        pct = min(35, 15 + (toplam // 50))
    elif toplam > 30 and commits >= 1:
        phase = "scaffold"
        pct = min(15, 5 + (kod // 5))
    elif toplam > 0:
        phase = "scaffold"
        pct = 5
    else:
        phase = "idea"
        pct = 0
    
    # Bonus puanlar
    if dosya_kontrol["tests"]:
        pct += 5
    if dosya_kontrol["dockerfile"]:
        pct += 3
    if dosya_kontrol["ci_cd"]:
        pct += 3
    if dosya_kontrol["hafiza"]:
        pct += 2
    if dosya_kontrol["anayasa"]:
        pct += 2
    if port_acik:
        pct += 5
    
    # Planning projeleri
    if status == "planning":
        phase = "idea" if toplam < 30 else "scaffold"
        pct = min(pct, 10)
    
    return phase, min(pct, 99)


def saglik_skoru(dosyalar: dict, git: dict, dosya_kontrol: dict) -> int:
    """0-100 arası sağlık skoru hesapla."""
    skor = 0
    
    # Dosya yapısı (max 25)
    if dosyalar["toplam"] > 0: skor += 5
    if dosyalar["kod"] > 10: skor += 5
    if dosyalar["kod"] > 50: skor += 5
    if dosyalar["test"] > 0: skor += 5
    if dosyalar["doc"] > 0: skor += 5
    
    # Git (max 25)
    if git["commit_sayisi"] > 0: skor += 5
    if git["commit_sayisi"] > 5: skor += 5
    if git["commit_sayisi"] > 20: skor += 5
    if git["aktif_gun"] > 1: skor += 5
    if git["branch"]: skor += 5
    
    # Kritik dosyalar (max 30)
    for key, val in dosya_kontrol.items():
        if val:
            skor += 4  # 8 kontrol × ~4 = ~30
    
    # Kod/test oranı (max 20)
    if dosyalar["kod"] > 0:
        test_oran = dosyalar["test"] / dosyalar["kod"]
        if test_oran > 0.1: skor += 10
        elif test_oran > 0.05: skor += 5
        
        # Config dosyası varlığı
        if dosyalar["config"] > 0: skor += 5
        if dosyalar["config"] > 3: skor += 5
    
    return min(skor, 100)


def projeleri_tara() -> list:
    """Tüm projeleri tara ve detaylı rapor üret."""
    with open(PROJECTS_JSON, "r", encoding="utf-8") as f:
        projeler = json.load(f)
    
    sonuclar = []
    
    for proje in projeler:
        pid = proje.get("id", "?")
        name = proje.get("name", "?")
        path = proje.get("path", "")
        status = proje.get("status", "?")
        local_port = proje.get("local_port")
        
        # Taramalar
        dosyalar = dosya_say(path)
        git = git_bilgisi(path)
        dosya_kontrol = onemli_dosya_kontrol(path)
        port_acik = port_kontrol(local_port)
        
        # Faz ve yüzde hesapla
        phase, completion = faz_belirle(proje, dosyalar, git, dosya_kontrol, port_acik)
        health = saglik_skoru(dosyalar, git, dosya_kontrol)
        
        sonuc = {
            "id": pid,
            "name": name,
            "status": status,
            "phase": phase,
            "completion_percent": completion,
            "health_score": health,
            "file_count": dosyalar["toplam"],
            "code_files": dosyalar["kod"],
            "test_files": dosyalar["test"],
            "doc_files": dosyalar["doc"],
            "commit_count": git["commit_sayisi"],
            "last_commit": git["son_commit_tarih"],
            "last_commit_msg": git["son_commit_mesaj"],
            "first_commit": git["ilk_commit_tarih"],
            "active_days": git["aktif_gun"],
            "branch": git["branch"],
            "port_running": port_acik,
            "has_readme": dosya_kontrol["readme"],
            "has_tests": dosya_kontrol["tests"],
            "has_docker": dosya_kontrol["dockerfile"],
            "has_ci_cd": dosya_kontrol["ci_cd"],
            "has_memory": dosya_kontrol["hafiza"],
            "has_anayasa": dosya_kontrol["anayasa"],
            "folder_exists": os.path.isdir(path),
        }
        
        sonuclar.append(sonuc)
    
    return sonuclar


def rapor_yazdir(sonuclar: list):
    """Terminal'e renkli rapor yazdır."""
    
    # Faz renkleri (ANSI)
    faz_renk = {
        "production": "\033[32m",  # yeşil
        "beta": "\033[36m",       # cyan
        "alpha": "\033[34m",      # mavi
        "mvp": "\033[33m",        # sarı
        "scaffold": "\033[35m",   # mor
        "idea": "\033[90m",       # gri
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    print(f"\n{BOLD}{'='*110}{RESET}")
    print(f"{BOLD}  EMARE EKOSİSTEMİ — PROJE DURUM RAPORU")
    print(f"  Tarih: {datetime.now().strftime('%d %B %Y %H:%M')}")
    print(f"  Toplam Proje: {len(sonuclar)}")
    print(f"{'='*110}{RESET}\n")
    
    # Başlık
    print(f"  {'#':<3} {'Proje':<28} {'Status':<12} {'Faz':<12} {'%':<5} {'Sağlık':<8} {'Dosya':<7} {'Kod':<6} {'Commit':<8} {'Son Aktivite':<20}")
    print(f"  {'-'*107}")
    
    # Faz bazlı gruplama
    for s in sonuclar:
        renk = faz_renk.get(s["phase"], "")
        
        health_bar = "█" * (s["health_score"] // 10) + "░" * (10 - s["health_score"] // 10)
        pct_bar = "▓" * (s["completion_percent"] // 10) + "░" * (10 - s["completion_percent"] // 10)
        
        last = s["last_commit"][:10] if s["last_commit"] else "—"
        
        print(f"  {sonuclar.index(s)+1:<3} {s['name']:<28} {s['status']:<12} {renk}{s['phase']:<12}{RESET} {pct_bar} {s['completion_percent']:>3}%  {health_bar} {s['health_score']:>3}  {s['file_count']:<7} {s['code_files']:<6} {s['commit_count']:<8} {last}")
    
    # Özet istatistikler
    print(f"\n{BOLD}  📊 ÖZET{RESET}")
    print(f"  {'─'*50}")
    
    # Faz dağılımı
    fazlar = {}
    for s in sonuclar:
        fazlar.setdefault(s["phase"], []).append(s["name"])
    
    for faz in ["production", "beta", "alpha", "mvp", "scaffold", "idea"]:
        if faz in fazlar:
            renk = faz_renk.get(faz, "")
            print(f"  {renk}{faz:<12}{RESET} ({len(fazlar[faz])}): {', '.join(fazlar[faz][:5])}{'...' if len(fazlar[faz])>5 else ''}")
    
    # Kritik eksikler
    print(f"\n{BOLD}  ⚠️  KRİTİK EKSİKLER{RESET}")
    print(f"  {'─'*50}")

    test_yok = [s["name"] for s in sonuclar if not s["has_tests"] and s["phase"] not in ("idea", "scaffold")]
    if test_yok:
        print(f"  🔴 Test yok ({len(test_yok)}): {', '.join(test_yok[:8])}")
    
    hafiza_yok = [s["name"] for s in sonuclar if not s["has_memory"]]
    if hafiza_yok:
        print(f"  🟠 Hafıza dosyası yok ({len(hafiza_yok)}): {', '.join(hafiza_yok[:8])}")
    
    anayasa_yok = [s["name"] for s in sonuclar if not s["has_anayasa"]]
    if anayasa_yok:
        print(f"  🟡 EMARE_ORTAK_CALISMA yok ({len(anayasa_yok)}): {', '.join(anayasa_yok[:8])}")
    
    docker_yok = [s["name"] for s in sonuclar if not s["has_docker"] and s["status"] == "production"]
    if docker_yok:
        print(f"  🟡 Production ama Docker yok ({len(docker_yok)}): {', '.join(docker_yok)}")
    
    tek_commit = [s["name"] for s in sonuclar if s["commit_count"] <= 1 and s["folder_exists"]]
    if tek_commit:
        print(f"  🔵 Tek commit (çeyiz push?) ({len(tek_commit)}): {', '.join(tek_commit[:8])}")
    
    # Ortalamalar
    avg_health = sum(s["health_score"] for s in sonuclar) / len(sonuclar)
    avg_completion = sum(s["completion_percent"] for s in sonuclar) / len(sonuclar)
    toplam_kod = sum(s["code_files"] for s in sonuclar)
    toplam_commit = sum(s["commit_count"] for s in sonuclar)
    
    print(f"\n{BOLD}  📈 İSTATİSTİK{RESET}")
    print(f"  {'─'*50}")
    print(f"  Ortalama Sağlık: {avg_health:.0f}/100")
    print(f"  Ortalama Tamamlanma: {avg_completion:.0f}%")
    print(f"  Toplam Kod Dosyası: {toplam_kod:,}")
    print(f"  Toplam Commit: {toplam_commit}")
    print(f"  Klasörü Olan: {sum(1 for s in sonuclar if s['folder_exists'])}/43")
    print()


def projects_json_guncelle(sonuclar: list):
    """projects.json'a yeni alanlar ekle."""
    with open(PROJECTS_JSON, "r", encoding="utf-8") as f:
        projeler = json.load(f)
    
    # Index oluştur
    sonuc_index = {s["id"]: s for s in sonuclar}
    
    for proje in projeler:
        pid = proje["id"]
        if pid in sonuc_index:
            s = sonuc_index[pid]
            proje["phase"] = s["phase"]
            proje["completion_percent"] = s["completion_percent"]
            proje["health_score"] = s["health_score"]
            proje["file_count"] = s["file_count"]
            proje["code_files"] = s["code_files"]
            proje["test_files"] = s["test_files"]
            proje["commit_count"] = s["commit_count"]
            proje["last_active"] = s["last_commit"]
            proje["scan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Yedek al
    yedek = PROJECTS_JSON.with_suffix(".json.bak")
    with open(yedek, "w", encoding="utf-8") as f:
        with open(PROJECTS_JSON, "r", encoding="utf-8") as orig:
            f.write(orig.read())
    
    # Güncelle
    with open(PROJECTS_JSON, "w", encoding="utf-8") as f:
        json.dump(projeler, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ projects.json güncellendi! (Yedek: {yedek.name})")
    return projeler


# ─── Ana Program ────────────────────────────────────────────

if __name__ == "__main__":
    print("🔍 Emare ekosistemi taranıyor...")
    sonuclar = projeleri_tara()
    
    if "--json" in sys.argv:
        print(json.dumps(sonuclar, indent=2, ensure_ascii=False, default=str))
    else:
        rapor_yazdir(sonuclar)
    
    if "--guncelle" in sys.argv:
        projects_json_guncelle(sonuclar)
