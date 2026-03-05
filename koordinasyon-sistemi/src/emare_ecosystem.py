"""
Emare Ekosistem Yöneticisi
===========================

21 Emare projesinin sağlık durumunu izler, EMARE_ORTAK_CALISMA
dosyalarını dağıtır ve senkronize tutar.

Bu modül daha önce manuel yapılan şu işleri otomatize eder:
- distribute_ortak_calisma.py  → /emare/distribute
- convert_to_symlink.py        → /emare/symlinks/repair
- create_dosya_yapisi.py       → /emare/dosya-yapisi/refresh
- Proje sağlık kontrolü        → /emare/health
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import structlog

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# Sabitler
# ─────────────────────────────────────────────────────────────────────────────

EMARE_ROOT = Path("/Users/emre/Desktop/Emare")
ORTAK_CALISMA_DIR = EMARE_ROOT / "EMARE_ORTAK_CALISMA"
PROJECTS_JSON = ORTAK_CALISMA_DIR / "projects.json"

# Ortak dağıtılacak dosyalar
ORTAK_FILES = [
    "README.md",
    "EMARE_ANAYASA.md",
    "EMARE_ORTAK_HAFIZA.md",
    "EMARE_AI_COLLECTIVE.md",
    "EMARE_ORTAK_TASARIM.md",
    "projects.json",
]

# Proje sağlığını gösteren dosya/klasörler (projenin aktif olduğunu kanıtlar)
HEALTH_INDICATORS = [
    "README.md", "main.py", "app.py", "index.js", "package.json",
    "composer.json", "artisan", "Dockerfile", "requirements.txt",
]


# ─────────────────────────────────────────────────────────────────────────────
# Veri sınıfları
# ─────────────────────────────────────────────────────────────────────────────

class ProjectHealth:
    """Bir projenin anlık sağlık durumu"""

    def __init__(self, project: Dict):
        self.id: str = project["id"]
        self.name: str = project["name"]
        self.path: Path = Path(project.get("path", ""))
        self.status_label: str = project.get("status", "unknown")
        self.category: str = project.get("category", "other")
        self.tech_stack: List[str] = project.get("tech_stack", [])

        # Anlık kontrol sonuçları
        self.exists: bool = False
        self.has_ortak_link: bool = False
        self.indicator_found: Optional[str] = None
        self.file_count: int = 0
        self.checked_at: datetime = datetime.now(timezone.utc)
        self.is_healthy: bool = False
        self.health_score: int = 0  # 0-100

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "status": self.status_label,
            "category": self.category,
            "exists": self.exists,
            "is_healthy": self.is_healthy,
            "health_score": self.health_score,
            "has_ortak_link": self.has_ortak_link,
            "indicator_found": self.indicator_found,
            "file_count": self.file_count,
            "checked_at": self.checked_at.isoformat(),
        }


class DistributeResult:
    """Dağıtım işlemi sonucu"""

    def __init__(self):
        self.total: int = 0
        self.success: int = 0
        self.skipped: int = 0
        self.failed: int = 0
        self.details: List[Dict] = []
        self.started_at: datetime = datetime.now(timezone.utc)
        self.finished_at: Optional[datetime] = None

    def finish(self):
        self.finished_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        duration = None
        if self.finished_at:
            duration = (self.finished_at - self.started_at).total_seconds()
        return {
            "total": self.total,
            "success": self.success,
            "skipped": self.skipped,
            "failed": self.failed,
            "duration_seconds": duration,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "details": self.details,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Ana sınıf
# ─────────────────────────────────────────────────────────────────────────────

class EmareEcosystemManager:
    """
    21 Emare projesini yöneten merkezi koordinatör.

    Sorumluluklar:
    1. Sağlık kontrolü (proje path'leri, ortak link'ler)
    2. EMARE_ORTAK_CALISMA dağıtımı (symlink veya kopya)
    3. DOSYA_YAPISI.md yenileme
    4. Symlink bütünlük kontrolü + onarımı
    5. Ekosistem özet raporu üretme
    """

    def __init__(self, projects_json_path: Optional[Path] = None):
        self.projects_json = projects_json_path or PROJECTS_JSON
        self.projects: List[Dict] = []
        self._load_projects()
        self._last_health: Optional[List[ProjectHealth]] = None
        self._last_health_time: Optional[datetime] = None

    def _load_projects(self):
        """projects.json'dan proje listesini yükle"""
        try:
            with open(self.projects_json, "r", encoding="utf-8") as f:
                self.projects = json.load(f)
            logger.info("ecosystem_projects_loaded", count=len(self.projects))
        except Exception as e:
            logger.error("failed_to_load_projects", error=str(e))
            self.projects = []

    # ── Sağlık Kontrolü ───────────────────────────────────────────────────────

    async def check_health(self, force: bool = False) -> List[ProjectHealth]:
        """
        Tüm 21 projenin sağlık durumunu kontrol et.

        force=False → son 60 saniye içinde kontrol edildiyse cache döndür.
        """
        now = datetime.now(timezone.utc)
        if (
            not force
            and self._last_health
            and self._last_health_time
            and (now - self._last_health_time).total_seconds() < 60
        ):
            return self._last_health

        results: List[ProjectHealth] = []

        async def check_one(project: Dict) -> ProjectHealth:
            health = ProjectHealth(project)
            path = health.path

            if not path or not path.exists():
                health.exists = False
                health.health_score = 0
                return health

            health.exists = True
            score = 40  # var olması 40 puan

            # Ortak calisma linki var mı?
            ortak_link = path / "EMARE_ORTAK_CALISMA"
            if ortak_link.exists():
                health.has_ortak_link = True
                score += 20

            # Bir sağlık indikatörü var mı?
            for indicator in HEALTH_INDICATORS:
                if (path / indicator).exists():
                    health.indicator_found = indicator
                    score += 20
                    break

            # Dosya sayısı
            try:
                health.file_count = sum(1 for _ in path.rglob("*") if _.is_file())
                if health.file_count > 0:
                    score += 20
            except Exception:
                pass

            health.health_score = min(score, 100)
            health.is_healthy = health.health_score >= 60
            return health

        # Paralel kontrol
        tasks = [check_one(p) for p in self.projects]
        results = await asyncio.gather(*tasks)

        self._last_health = list(results)
        self._last_health_time = now

        healthy = sum(1 for h in results if h.is_healthy)
        logger.info(
            "ecosystem_health_checked",
            total=len(results),
            healthy=healthy,
            unhealthy=len(results) - healthy,
        )
        return list(results)

    def get_health_summary(self, results: List[ProjectHealth]) -> Dict:
        """Sağlık sonuçlarından özet üret"""
        total = len(results)
        healthy = sum(1 for h in results if h.is_healthy)
        missing = sum(1 for h in results if not h.exists)
        no_link = sum(1 for h in results if h.exists and not h.has_ortak_link)
        avg_score = sum(h.health_score for h in results) / total if total else 0

        return {
            "total_projects": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "missing_path": missing,
            "no_ortak_link": no_link,
            "avg_health_score": round(avg_score, 1),
            "ecosystem_status": (
                "healthy" if healthy == total
                else "degraded" if healthy >= total * 0.7
                else "critical"
            ),
        }

    # ── Dağıtım ───────────────────────────────────────────────────────────────

    async def distribute_ortak_calisma(
        self, method: str = "symlink", force: bool = False
    ) -> DistributeResult:
        """
        EMARE_ORTAK_CALISMA dosyalarını tüm projelere dağıt.

        method="symlink" → EMARE_ORTAK_CALISMA klasörünü proje altına symlink et
        method="copy"    → Dosyaları kopyala (symlink desteklenmiyorsa)
        force=True       → Mevcut link/kopya üzerine yaz
        """
        result = DistributeResult()
        result.total = len(self.projects)

        if not ORTAK_CALISMA_DIR.exists():
            result.finish()
            return result

        async def distribute_one(project: Dict):
            detail: Dict[str, Any] = {"id": project["id"], "name": project["name"]}
            path_str = project.get("path", "")
            if not path_str:
                detail["status"] = "skipped"
                detail["reason"] = "path tanımsız"
                result.skipped += 1
                result.details.append(detail)
                return

            proj_path = Path(path_str)
            if not proj_path.exists():
                detail["status"] = "skipped"
                detail["reason"] = "proje klasörü yok"
                result.skipped += 1
                result.details.append(detail)
                return

            link_target = proj_path / "EMARE_ORTAK_CALISMA"

            try:
                if method == "symlink":
                    if link_target.exists() or link_target.is_symlink():
                        if not force:
                            detail["status"] = "skipped"
                            detail["reason"] = "zaten mevcut"
                            result.skipped += 1
                            result.details.append(detail)
                            return
                        # Mevcut linki sil
                        if link_target.is_symlink():
                            link_target.unlink()
                        elif link_target.is_dir():
                            import shutil
                            shutil.rmtree(link_target)

                    link_target.symlink_to(ORTAK_CALISMA_DIR)
                    detail["status"] = "success"
                    detail["method"] = "symlink"
                    result.success += 1

                else:  # copy
                    import shutil
                    if link_target.exists() and not force:
                        detail["status"] = "skipped"
                        detail["reason"] = "zaten mevcut"
                        result.skipped += 1
                        result.details.append(detail)
                        return
                    if link_target.exists():
                        shutil.rmtree(link_target)
                    shutil.copytree(ORTAK_CALISMA_DIR, link_target)
                    detail["status"] = "success"
                    detail["method"] = "copy"
                    result.success += 1

            except Exception as e:
                detail["status"] = "failed"
                detail["error"] = str(e)
                result.failed += 1

            result.details.append(detail)

        await asyncio.gather(*[distribute_one(p) for p in self.projects])
        result.finish()

        logger.info(
            "ortak_calisma_distributed",
            success=result.success,
            skipped=result.skipped,
            failed=result.failed,
        )
        return result

    # ── Symlink Onarımı ───────────────────────────────────────────────────────

    async def repair_symlinks(self) -> Dict:
        """
        Kırık symlink'leri tespit et ve onar.
        Ortak Calisma'ya işaret eden tüm symlinkleri kontrol eder.
        """
        broken: List[str] = []
        repaired: List[str] = []
        healthy_links: List[str] = []

        for project in self.projects:
            path_str = project.get("path", "")
            if not path_str:
                continue
            proj_path = Path(path_str)
            link = proj_path / "EMARE_ORTAK_CALISMA"

            if link.is_symlink():
                if link.exists():
                    healthy_links.append(project["id"])
                else:
                    # Kırık symlink
                    broken.append(project["id"])
                    try:
                        link.unlink()
                        link.symlink_to(ORTAK_CALISMA_DIR)
                        repaired.append(project["id"])
                    except Exception as e:
                        logger.warning("symlink_repair_failed", project=project["id"], error=str(e))

        return {
            "healthy_links": len(healthy_links),
            "broken_found": len(broken),
            "repaired": len(repaired),
            "repair_failed": len(broken) - len(repaired),
            "repaired_ids": repaired,
        }

    # ── DOSYA_YAPISI.md Yenileme ──────────────────────────────────────────────

    async def refresh_dosya_yapisi(self) -> Dict:
        """
        Tüm projeler için DOSYA_YAPISI.md'yi yenile.
        Her projenin kök klasöründeki dosya/klasör yapısını README formatında yazar.
        """
        updated: List[str] = []
        skipped: List[str] = []
        failed: List[str] = []

        for project in self.projects:
            path_str = project.get("path", "")
            if not path_str:
                skipped.append(project["id"])
                continue
            proj_path = Path(path_str)
            if not proj_path.exists():
                skipped.append(project["id"])
                continue

            try:
                tree_lines = self._build_tree(proj_path, max_depth=3)
                content = self._render_dosya_yapisi(project, tree_lines)
                target = proj_path / "DOSYA_YAPISI.md"
                target.write_text(content, encoding="utf-8")
                updated.append(project["id"])
            except Exception as e:
                logger.warning("dosya_yapisi_failed", project=project["id"], error=str(e))
                failed.append(project["id"])

        logger.info("dosya_yapisi_refreshed", updated=len(updated), skipped=len(skipped), failed=len(failed))
        return {
            "updated": len(updated),
            "skipped": len(skipped),
            "failed": len(failed),
            "updated_ids": updated,
        }

    def _build_tree(self, path: Path, max_depth: int = 3, prefix: str = "", depth: int = 0) -> List[str]:
        """Basit dosya ağacı oluştur"""
        lines: List[str] = []
        if depth > max_depth:
            return lines

        # Gizli ve gereksiz klasörleri atla
        SKIP = {"__pycache__", ".git", "node_modules", "vendor", ".venv", "venv", ".idea", ".DS_Store"}

        try:
            entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            return lines

        for i, entry in enumerate(entries):
            if entry.name in SKIP or entry.name.startswith("."):
                continue
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir() and depth < max_depth:
                extension = "    " if i == len(entries) - 1 else "│   "
                lines.extend(self._build_tree(entry, max_depth, prefix + extension, depth + 1))
        return lines

    def _render_dosya_yapisi(self, project: Dict, tree_lines: List[str]) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        name = project["name"]
        pid = project["id"]
        status = project.get("status", "unknown")
        tech = ", ".join(project.get("tech_stack", []))
        desc = project.get("description", "")

        lines = [
            f"# {name} — Dosya Yapısı",
            "",
            f"> 🕒 Son güncelleme: {now}  ",
            f"> 🆔 ID: `{pid}` | Durum: `{status}`  ",
            f"> 🔧 Tech: {tech or 'belirtilmemiş'}",
            "",
            f"## Açıklama",
            "",
            desc or "_Açıklama eklenmemiş._",
            "",
            "## Klasör Yapısı",
            "",
            "```",
            f"{project.get('path', pid)}/",
        ]
        lines += tree_lines
        lines += [
            "```",
            "",
            "---",
            f"_Bu dosya emarework tarafından otomatik üretilmiştir._",
        ]
        return "\n".join(lines) + "\n"

    # ── Ekosistem Özeti ───────────────────────────────────────────────────────

    async def get_ecosystem_overview(self) -> Dict:
        """Tüm ekosisteme genel bakış — dashboard için"""
        health_results = await self.check_health()
        summary = self.get_health_summary(health_results)

        # Kategorilere göre dağılım
        by_category: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for p in self.projects:
            cat = p.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + 1
            st = p.get("status", "unknown")
            by_status[st] = by_status.get(st, 0) + 1

        return {
            "summary": summary,
            "by_category": by_category,
            "by_status": by_status,
            "ortak_calisma": {
                "path": str(ORTAK_CALISMA_DIR),
                "exists": ORTAK_CALISMA_DIR.exists(),
                "files": [f for f in ORTAK_FILES if (ORTAK_CALISMA_DIR / f).exists()],
            },
            "projects": [h.to_dict() for h in health_results],
        }

    async def get_project_detail(self, project_id: str) -> Optional[Dict]:
        """Tek proje detayı"""
        project = next((p for p in self.projects if p["id"] == project_id), None)
        if not project:
            return None

        health = await self.check_health()
        h = next((x for x in health if x.id == project_id), None)

        result = dict(project)
        if h:
            result["health"] = h.to_dict()
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_ecosystem: Optional[EmareEcosystemManager] = None


def get_ecosystem() -> EmareEcosystemManager:
    global _ecosystem
    if _ecosystem is None:
        _ecosystem = EmareEcosystemManager()
    return _ecosystem
