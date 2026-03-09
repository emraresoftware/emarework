"""
Emare AI Workers  (v2)
======================

projects.json'dan 43 AI worker'ı yükler ve yönetir.

Yenilikler (v2):
- Genişletilmiş uzmanlık haritası — 43 projenin tüm tech stack'i kapsandı
- is_running()       → local portunu TCP ping ile kontrol eder
- start_locally()    → local_start_cmd ile projeyi başlatır
- read_memory()      → hafıza MD dosyasını okur / snippet döndürür
- match_score()      → task gereksinimleriyle overlap skoru
- EmareAIWorkforce.reload()            → sıcak yeniden yükle
- EmareAIWorkforce.find_by_category()  → kategori filtresi
- EmareAIWorkforce.get_by_name()       → isim ile ara (case-insensitive)
- EmareAIWorkforce.running_workers()   → çalışan projeleri bul (async)
- EmareAIWorkforce.find_workers_with_scores() → skor + worker dict
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# Uzmanlık Haritası  —  tüm 43 projenin tech stack'i buraya yansıtılıyor
# ─────────────────────────────────────────────────────────────────────────────

_TECH_EXPERTISE: Dict[str, List[str]] = {
    # Diller
    "Python":        ["python", "backend"],
    "PHP":           ["php", "backend"],
    "Laravel 12":    ["php", "laravel", "backend"],
    "Laravel":       ["php", "laravel", "backend"],
    "Node.js":       ["nodejs", "backend", "javascript"],
    "TypeScript":    ["typescript", "javascript", "frontend"],
    "Rust":          ["rust", "systems"],
    "C (C11)":       ["c", "systems"],
    "Go":            ["go", "backend"],
    # Web & API
    "FastAPI":       ["fastapi", "backend", "api"],
    "Flask":         ["flask", "backend", "api"],
    "Django":        ["django", "backend", "api"],
    "Express.js":    ["nodejs", "backend", "api"],
    # Frontend
    "React":         ["react", "frontend", "javascript"],
    "React 19":      ["react", "frontend", "javascript"],
    "Next.js":       ["nextjs", "react", "frontend"],
    "Vue":           ["vue", "frontend", "javascript"],
    "Alpine.js":     ["javascript", "frontend"],
    "Tailwind CSS":  ["css", "frontend"],
    "Bootstrap 5":   ["css", "frontend"],
    "Vanilla JS":    ["javascript", "frontend"],
    "xterm.js":      ["javascript", "frontend"],
    # AI & ML
    "Gemini AI":     ["ai", "llm", "gemini"],
    "Gemini":        ["ai", "llm", "gemini"],
    "OpenAI":        ["ai", "llm", "openai"],
    "OpenAI gpt-4o": ["ai", "llm", "openai"],
    "LangGraph":     ["ai", "langchain", "multi-agent"],
    "Claude 3.5 Sonnet": ["ai", "llm", "claude"],
    "GPT-4o":        ["ai", "llm", "openai"],
    "LLaMA":         ["ai", "llm", "local-ai"],
    "Mistral":       ["ai", "llm", "local-ai"],
    "vLLM":          ["ai", "llm", "local-ai"],
    "Ollama":        ["ai", "llm", "local-ai"],
    "PyTorch":       ["ml", "ai", "deep-learning"],
    "WhatsApp Bridge": ["ai", "messaging", "automation"],
    "Trendyol Seller API": ["ecommerce", "api", "automation"],
    # Veritabanı
    "PostgreSQL":    ["database", "sql"],
    "PostgreSQL 16": ["database", "sql"],
    "MySQL":         ["database", "sql"],
    "MariaDB":       ["database", "sql"],
    "SQLite":        ["database", "sql", "sqlite"],
    "Neo4j":         ["database", "graph-db"],
    "PGVector":      ["database", "vector-db"],
    "B+Tree":        ["database", "systems"],
    "WAL":           ["database", "systems"],
    "ACID":          ["database", "systems"],
    "Redis 7":       ["database", "redis", "cache"],
    "Redis":         ["database", "redis", "cache"],
    # Altyapı & DevOps
    "Docker":        ["docker", "devops"],
    "Nginx":         ["nginx", "devops"],
    "Celery":        ["celery", "async", "devops"],
    "SQLAlchemy":    ["orm", "database"],
    "Alembic":       ["database", "migrations"],
    "Paramiko":      ["ssh", "devops"],
    "Guzzle":        ["http", "php"],
    "Chart.js":      ["charts", "frontend"],
    "DataTables":    ["frontend", "table"],
    "pytest":        ["testing"],
    "GitPython":     ["git", "devops"],
    # Platform & Protokol
    "WebSocket":     ["websocket", "realtime"],
    "SocketIO":      ["websocket", "realtime"],
    "Chrome Extension": ["browser-extension", "javascript"],
    "Chrome Extension API": ["browser-extension", "javascript"],
    "Asterisk":      ["voip", "telephony"],
    "Webpack":       ["bundler", "javascript"],
    "Jinja2":        ["templating", "python"],
    # Düşük Seviye
    "QEMU":          ["virtualization", "systems"],
    "NeuroKernel":   ["systems", "os"],
    "Bare Metal":    ["systems", "os"],
    "AI Scheduler":  ["ai", "systems"],
    "pthread":       ["systems", "concurrency"],
    "Pillow":        ["image-processing", "python"],
    "mss":           ["screen-capture", "python"],
    "pyautogui":     ["automation", "python"],
    "difflib":       ["python", "text-processing"],
}

_CATEGORY_EXPERTISE: Dict[str, List[str]] = {
    "SaaS Platform":  ["saas", "backend", "api"],
    "Infrastructure": ["devops", "infrastructure"],
    "Security":       ["security", "penetration-testing"],
    "Automation":     ["automation"],
    "POS":            ["pos", "ecommerce", "backend"],
    "Tool":           ["tools"],
    "Core Engine":    ["systems", "performance"],
}


# ─────────────────────────────────────────────────────────────────────────────
# EmareAIWorker
# ─────────────────────────────────────────────────────────────────────────────

class EmareAIWorker:
    """Tek bir Emare projesini temsil eden AI worker."""

    def __init__(self, project_data: Dict):
        self.id: str          = project_data["id"]
        self.name: str        = project_data["name"]
        self.icon: str        = project_data.get("icon", "🤖")
        self.color: str       = project_data.get("color", "#6366f1")
        self.description: str = project_data.get("description", "")
        self.status: str      = project_data.get("status", "development")
        self.category: str    = project_data.get("category", "General")
        self.notes: List[str] = project_data.get("notes", [])

        self.tech: List[str]             = project_data.get("tech", [])
        self.path: Optional[str]         = project_data.get("path")
        self.memory_file: Optional[str]  = project_data.get("memory_file")
        self.local_start_cmd: Optional[str] = project_data.get("local_start_cmd")
        self.local_port: Optional[int]      = project_data.get("local_port")
        self.url: Optional[str]             = project_data.get("url")
        self.server: Optional[Dict]         = project_data.get("server")

        self.expertise: List[str] = self._determine_expertise()
        self.priority: int        = self._calculate_priority()
        self.availability: bool   = self.status in ("production", "ready")

    # ── Expertise & Priority ──────────────────────────────────────────────────

    def _determine_expertise(self) -> List[str]:
        skills: set = set()
        for tech in self.tech:
            mapped = _TECH_EXPERTISE.get(tech, [])
            skills.update(mapped)
            if not mapped:
                lower = tech.lower()
                for key, values in _TECH_EXPERTISE.items():
                    if key.lower() in lower or lower in key.lower():
                        skills.update(values)
                        break
        skills.update(_CATEGORY_EXPERTISE.get(self.category, []))
        return sorted(skills)

    def _calculate_priority(self) -> int:
        """
        Öncelik skoru (1–10).
        production +3 | ready +2 | development +1
        tech sayısı her 2 için +1 (max +3)
        expertise genişliği her 4 için +1 (max +2)
        aktif notlar: +1
        """
        score = 4
        score += {"production": 3, "ready": 2, "development": 1}.get(self.status, 0)
        score += min(len(self.tech) // 2, 3)
        score += min(len(self.expertise) // 4, 2)
        if self.notes:
            score += 1
        return min(score, 10)

    # ── Task Eşleşmesi ────────────────────────────────────────────────────────

    def can_handle_task(self, requirements: List[str]) -> bool:
        req_lower = [r.lower() for r in requirements]
        exp_lower = [e.lower() for e in self.expertise]
        return any(r in exp_lower for r in req_lower)

    def match_score(self, requirements: List[str]) -> int:
        """Uzmanlık örtüşme skoru — overlap × 10 + priority."""
        req_lower = {r.lower() for r in requirements}
        exp_lower = {e.lower() for e in self.expertise}
        return len(req_lower & exp_lower) * 10 + self.priority

    # ── Çalışma Durumu ────────────────────────────────────────────────────────

    async def is_running(self, timeout: float = 1.5) -> bool:
        """local_port'u TCP ping ile kontrol et."""
        if not self.local_port:
            return False
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", self.local_port),
                timeout=timeout,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    def start_locally(self, wait: bool = False) -> Optional[subprocess.Popen]:
        """local_start_cmd ile projeyi arka planda başlat."""
        if not self.local_start_cmd:
            logger.warning("no_start_cmd", worker=self.id)
            return None
        logger.info("starting_worker", worker=self.id)
        proc = subprocess.Popen(
            self.local_start_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if wait:
            proc.wait()
        return proc

    # ── Hafıza Dosyası ────────────────────────────────────────────────────────

    def read_memory(self, max_lines: int = 50) -> Optional[str]:
        """memory_file MD'sini oku. max_lines=0 → tüm dosya."""
        if not self.memory_file:
            return None
        path = Path(self.memory_file)
        if not path.exists():
            return None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            if max_lines and len(lines) > max_lines:
                lines = lines[:max_lines] + [f"\n… (+{len(lines) - max_lines} satır daha)"]
            return "\n".join(lines)
        except Exception as e:
            logger.warning("memory_read_failed", worker=self.id, error=str(e))
            return None

    # ── Serileştirme ──────────────────────────────────────────────────────────

    def to_dict(self, include_memory: bool = False) -> Dict:
        data = {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "description": self.description,
            "status": self.status,
            "category": self.category,
            "tech": self.tech,
            "expertise": self.expertise,
            "priority": self.priority,
            "availability": self.availability,
            "path": self.path,
            "local_port": self.local_port,
            "local_start_cmd": self.local_start_cmd,
            "url": self.url,
            "server": self.server,
            "memory_file": self.memory_file,
            "notes": self.notes,
        }
        if include_memory:
            data["memory_snippet"] = self.read_memory(max_lines=30)
        return data

    def __repr__(self) -> str:
        return f"<EmareAIWorker id={self.id!r} priority={self.priority} expertise={len(self.expertise)}>"


# ─────────────────────────────────────────────────────────────────────────────
# EmareAIWorkforce
# ─────────────────────────────────────────────────────────────────────────────

class EmareAIWorkforce:
    """Tüm 43 AI worker'ı yönetir."""

    def __init__(self, projects_json_path: str):
        self.projects_json_path = projects_json_path
        self.workers: List[EmareAIWorker] = []
        self.load_workers()

    def load_workers(self) -> None:
        try:
            with open(self.projects_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.workers = [EmareAIWorker(p) for p in data]
            logger.info(
                "workers_loaded",
                total=len(self.workers),
                production=sum(1 for w in self.workers if w.status == "production"),
                ready=sum(1 for w in self.workers if w.status == "ready"),
                development=sum(1 for w in self.workers if w.status == "development"),
            )
        except Exception as e:
            logger.error("load_workers_failed", error=str(e))
            raise

    def reload(self) -> None:
        """projects.json değişti — sıcak yeniden yükle."""
        logger.info("workforce_reloading")
        self.load_workers()

    # ── Sorgulama ─────────────────────────────────────────────────────────────

    def get_available_workers(self) -> List[EmareAIWorker]:
        return [w for w in self.workers if w.availability]

    def get_by_id(self, worker_id: str) -> Optional[EmareAIWorker]:
        return next((w for w in self.workers if w.id == worker_id), None)

    def get_worker_by_id(self, worker_id: str) -> Optional[EmareAIWorker]:
        """Geriye uyumluluk için alias."""
        return self.get_by_id(worker_id)

    def get_by_name(self, name: str) -> Optional[EmareAIWorker]:
        """İsim ile ara (case-insensitive, kısmi eşleşme)."""
        lower = name.lower()
        return next((w for w in self.workers if lower in w.name.lower()), None)

    def find_by_category(self, category: str) -> List[EmareAIWorker]:
        lower = category.lower()
        return [w for w in self.workers if w.category.lower() == lower]

    def find_by_expertise(self, skill: str) -> List[EmareAIWorker]:
        lower = skill.lower()
        return [w for w in self.workers if lower in [e.lower() for e in w.expertise]]

    # ── Görev Eşleştirme ─────────────────────────────────────────────────────

    def find_best_workers_for_task(
        self,
        task_requirements: List[str],
        max_workers: int = 5,
        only_available: bool = False,
    ) -> List[EmareAIWorker]:
        """Gereksinimlerle en iyi örtüşen worker'ları sıralı döndür."""
        pool = self.get_available_workers() if only_available else self.workers
        scored: List[Tuple[int, EmareAIWorker]] = [
            (w.match_score(task_requirements), w)
            for w in pool
            if w.can_handle_task(task_requirements)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [w for _, w in scored[:max_workers]]

    def find_workers_with_scores(
        self,
        task_requirements: List[str],
        max_workers: int = 5,
    ) -> List[Dict]:
        """find_best_workers_for_task + match_score dahil dict listesi."""
        pool = self.workers
        scored: List[Tuple[int, EmareAIWorker]] = [
            (w.match_score(task_requirements), w)
            for w in pool
            if w.can_handle_task(task_requirements)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {**w.to_dict(), "match_score": score}
            for score, w in scored[:max_workers]
        ]

    # ── Async: Çalışanları tespit et ─────────────────────────────────────────

    async def running_workers(self) -> List[Dict]:
        """Local portuna TCP bağlantısı başarılı olan worker'ları döndür."""
        async def check(w: EmareAIWorker) -> Optional[Dict]:
            if await w.is_running():
                return {
                    "id": w.id, "name": w.name, "icon": w.icon,
                    "port": w.local_port, "url": w.url,
                }
            return None

        results = await asyncio.gather(*[check(w) for w in self.workers])
        return [r for r in results if r is not None]

    # ── İstatistikler ─────────────────────────────────────────────────────────

    def get_workforce_stats(self) -> Dict:
        by_status: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_expertise: Dict[str, int] = {}

        for w in self.workers:
            by_status[w.status] = by_status.get(w.status, 0) + 1
            by_category[w.category] = by_category.get(w.category, 0) + 1
            for skill in w.expertise:
                by_expertise[skill] = by_expertise.get(skill, 0) + 1

        top_skills = sorted(by_expertise.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_workers": len(self.workers),
            "available_workers": len(self.get_available_workers()),
            "by_status": by_status,
            "by_category": by_category,
            "by_expertise": dict(top_skills),
            "top_priority_workers": [
                {"id": w.id, "name": w.name, "priority": w.priority}
                for w in sorted(self.workers, key=lambda x: x.priority, reverse=True)[:5]
            ],
        }

    def __repr__(self) -> str:
        return f"<EmareAIWorkforce workers={len(self.workers)} available={len(self.get_available_workers())}>"


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_workforce: Optional[EmareAIWorkforce] = None
_DEFAULT_JSON = (
    Path(__file__).parent.parent.parent.parent / "projects.json"
)


def get_workforce(projects_json_path: Optional[str] = None) -> EmareAIWorkforce:
    """Workforce singleton'ını döndür (ilk çağrıda oluşturur)."""
    global _workforce
    if _workforce is None:
        _workforce = EmareAIWorkforce(projects_json_path or str(_DEFAULT_JSON))
    return _workforce


def reload_workforce() -> EmareAIWorkforce:
    """projects.json güncellendiğinde singleton'ı sıcak yeniden yükle."""
    global _workforce
    if _workforce:
        _workforce.reload()
    else:
        _workforce = EmareAIWorkforce(str(_DEFAULT_JSON))
    return _workforce


if __name__ == "__main__":
    # Test
    workforce = get_workforce()
    
    print(f"\n🤖 Emare AI Workforce")
    print(f"{'='*50}")
    print(f"Toplam AI: {len(workforce.workers)}")
    print(f"Aktif AI: {len(workforce.get_available_workers())}")
    
    print(f"\n📊 İstatistikler:")
    stats = workforce.get_workforce_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n🎯 Backend task için en iyi 3 AI:")
    best = workforce.find_best_workers_for_task(["backend", "python"], max_workers=3)
    for i, worker in enumerate(best, 1):
        print(f"  {i}. {worker.icon} {worker.name} (Priority: {worker.priority})")
        print(f"     Expertise: {', '.join(worker.expertise)}")
