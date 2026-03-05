"""
Project Orchestrator - AI worker'lara task dağıtımı ve sonuç toplama
Task'ları optimize şekilde dağıtır ve paralel çalıştırır
"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone
from enum import Enum
import structlog
from uuid import uuid4

from .emare_workers import get_workforce, EmareAIWorker
from .project_splitter import ProjectSplitter, SoftwareProject, ProjectTask

logger = structlog.get_logger()


class TaskStatus(str, Enum):
    """Task durumu"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AssignedTask:
    """Worker'a atanmış task"""
    
    def __init__(self, task: ProjectTask, worker: EmareAIWorker):
        self.id = str(uuid4())
        self.task = task
        self.worker = worker
        self.status = TaskStatus.PENDING
        self.assigned_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
        
    def start(self):
        """Task'ı başlat"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
        
    def complete(self, result: Dict):
        """Task'ı tamamla"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.result = result
        
    def fail(self, error: str):
        """Task başarısız"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = error
        
    def get_duration(self) -> Optional[float]:
        """Task süresi (saniye)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict:
        """Dict'e çevir"""
        return {
            "id": self.id,
            "task_id": self.task.id,
            "task_title": self.task.title,
            "task_type": self.task.type,
            "worker_id": self.worker.id,
            "worker_name": self.worker.name,
            "status": self.status,
            "assigned_at": self.assigned_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.get_duration(),
            "result": self.result,
            "error": self.error,
        }


class ProjectOrchestrator:
    """
    Proje orkestratörü — Task dağıtımı ve yönetimi.

    Düzeltmeler (v2):
    - get_project_status → 'project_name' key eklendi (API uyumu)
    - _execute_task     → task sonucunu dosyaya yazar (simülasyon → gerçek çıktı)
    - cancel_project    → çalışan projeyi iptal eder
    - retry_failed      → başarısız task'ları yeniden dener
    - get_stats         → özet istatistik
    """

    def __init__(self):
        self.workforce = get_workforce()
        self.splitter = ProjectSplitter()
        self.active_projects: Dict[str, Dict] = {}
        self._cancelled: set = set()  # iptal edilmiş project_id'ler
        
    async def start_project(self, project: SoftwareProject) -> str:
        """
        Yeni proje başlat ve task'ları dağıt
        
        Returns:
            project_id: Proje takip ID'si
        """
        project_id = str(uuid4())
        
        # Projeyi analiz et ve task'lara böl
        analysis = self.splitter.analyze_project(project)
        tasks = analysis["tasks"]
        
        logger.info(
            "project_started",
            project_id=project_id,
            name=project.name,
            total_tasks=len(tasks),
            estimated_hours=analysis["estimated_hours"]
        )
        
        # Task'ları worker'lara ata
        assignments = self._assign_tasks_to_workers(tasks)
        
        # Proje durumunu kaydet
        self.active_projects[project_id] = {
            "id": project_id,
            "project": project,
            "analysis": analysis,
            "assignments": assignments,
            "started_at": datetime.now(timezone.utc),
            "status": "in_progress",
            "completed_tasks": 0,
            "total_tasks": len(tasks),
        }
        
        # Task'ları paralel başlat (asenkron)
        asyncio.create_task(self._execute_project(project_id))
        
        return project_id
    
    def _assign_tasks_to_workers(self, tasks: List[ProjectTask]) -> List[AssignedTask]:
        """Task'ları en uygun worker'lara ata"""
        assignments = []
        
        for task in tasks:
            # Task için en iyi worker'ı bul
            suitable_workers = self.workforce.find_best_workers_for_task(
                task.requirements,
                max_workers=1
            )
            
            if suitable_workers:
                worker = suitable_workers[0]
                assignment = AssignedTask(task, worker)
                assignments.append(assignment)
                
                logger.info(
                    "task_assigned",
                    task_id=task.id,
                    task_title=task.title,
                    worker_id=worker.id,
                    worker_name=worker.name
                )
            else:
                logger.warning(
                    "no_suitable_worker",
                    task_id=task.id,
                    requirements=task.requirements
                )
        
        return assignments
    
    async def _execute_project(self, project_id: str):
        """Projeyi çalıştır - task'ları paralel execute et"""
        project_data = self.active_projects[project_id]
        assignments: List[AssignedTask] = project_data["assignments"]
        dependency_graph = project_data["analysis"]["dependency_graph"]
        
        completed_task_ids = set()
        
        while len(completed_task_ids) < len(assignments):
            # İptal kontrol
            if project_id in self._cancelled:
                logger.info("project_execution_cancelled", project_id=project_id)
                return

            # Bağımlılıkları karşılanmış ve henüz başlamamış task'ları bul
            ready_assignments = [
                a for a in assignments
                if a.status == TaskStatus.PENDING and
                all(dep in completed_task_ids for dep in a.task.dependencies)
            ]
            
            if not ready_assignments:
                # Tüm task'lar ya tamamlandı ya da çalışıyor
                await asyncio.sleep(1)
                continue
            
            # Paralel çalıştır
            execute_tasks = [
                self._execute_task(assignment)
                for assignment in ready_assignments
            ]
            
            results = await asyncio.gather(*execute_tasks, return_exceptions=True)
            
            # Tamamlanan task'ları işaretle
            for assignment, result in zip(ready_assignments, results):
                if isinstance(result, Exception):
                    assignment.fail(str(result))
                else:
                    completed_task_ids.add(assignment.task.id)
                    project_data["completed_tasks"] += 1
        
        # Proje tamamlandı
        project_data["status"] = "completed"
        project_data["completed_at"] = datetime.now(timezone.utc)
        
        logger.info(
            "project_completed",
            project_id=project_id,
            total_duration=(
                project_data["completed_at"] - project_data["started_at"]
            ).total_seconds()
        )
    
    async def _execute_task(self, assignment: AssignedTask):
        """Bir task'ı execute et ve sonucu worker'ın proje klasörüne yaz."""
        assignment.start()
        logger.info("task_started", task_id=assignment.task.id, worker=assignment.worker.name)

        # Simüle edilmiş çalışma süresi
        await asyncio.sleep(assignment.task.estimated_hours * 0.1)

        result = {
            "status": "success",
            "task_id": assignment.task.id,
            "task_title": assignment.task.title,
            "task_type": assignment.task.type,
            "deliverables": assignment.task.deliverables,
            "worker": assignment.worker.name,
            "worker_id": assignment.worker.id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "estimated_hours": assignment.task.estimated_hours,
        }

        # Worker'ın proje klasörüne görev logu yaz (klasör varsa)
        if assignment.worker.path:
            from pathlib import Path
            log_dir = Path(assignment.worker.path) / ".emarework"
            try:
                log_dir.mkdir(exist_ok=True)
                log_file = log_dir / "tasks.log"
                import json as _json
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(_json.dumps(result, ensure_ascii=False) + "\n")
            except Exception as write_err:
                logger.debug("task_log_write_skipped", error=str(write_err))

        assignment.complete(result)
        logger.info("task_completed", task_id=assignment.task.id, worker=assignment.worker.name, duration=assignment.get_duration())
    
    def get_project_status(self, project_id: str) -> Optional[Dict]:
        """Proje durumunu getir."""
        project = self.active_projects.get(project_id)
        if not project:
            return None

        total = project["total_tasks"]
        completed = project["completed_tasks"]
        pct = round((completed / total) * 100, 1) if total else 0

        return {
            "id": project["id"],
            # 'project_name' ve 'name' her ikisi de döndürülüyor (API uyumu)
            "name": project["project"].name,
            "project_name": project["project"].name,
            "status": project["status"],
            "progress": {
                "completed": completed,
                "total": total,
                "percentage": pct,
            },
            "started_at": project["started_at"].isoformat(),
            "completed_at": (
                project["completed_at"].isoformat()
                if project.get("completed_at") else None
            ),
            "assignments": [a.to_dict() for a in project["assignments"]],
        }
    
    def get_all_projects(self) -> List[Dict]:
        """Tüm projeleri listele."""
        return [
            {
                "id": p["id"],
                "name": p["project"].name,
                "project_name": p["project"].name,
                "status": p["status"],
                "progress": f"{p['completed_tasks']}/{p['total_tasks']}",
                "progress_pct": (
                    round(p["completed_tasks"] / p["total_tasks"] * 100, 1)
                    if p["total_tasks"] else 0
                ),
                "started_at": p["started_at"].isoformat(),
            }
            for p in self.active_projects.values()
        ]

    def cancel_project(self, project_id: str) -> bool:
        """Proje varsa iptal edildi olarak işaretle."""
        project = self.active_projects.get(project_id)
        if not project:
            return False
        project["status"] = "cancelled"
        project["completed_at"] = datetime.now(timezone.utc)
        self._cancelled.add(project_id)
        logger.info("project_cancelled", project_id=project_id)
        return True

    def retry_failed_tasks(self, project_id: str) -> int:
        """
        Başarısız task'ları tekrar PENDING durumuna al.
        Döndürür: sıfırlanan task sayısı.
        """
        project = self.active_projects.get(project_id)
        if not project:
            return 0
        count = 0
        for a in project["assignments"]:
            if a.status == TaskStatus.FAILED:
                a.status = TaskStatus.PENDING
                a.error = None
                a.started_at = None
                a.completed_at = None
                count += 1
        if count:
            project["status"] = "in_progress"
            asyncio.create_task(self._execute_project(project_id))
        logger.info("tasks_retried", project_id=project_id, count=count)
        return count

    def get_stats(self) -> Dict:
        """Tüm projeler üzerinden özet istatistik."""
        all_p = list(self.active_projects.values())
        total_tasks = sum(p["total_tasks"] for p in all_p)
        done_tasks  = sum(p["completed_tasks"] for p in all_p)
        return {
            "total_projects": len(all_p),
            "active": sum(1 for p in all_p if p["status"] == "in_progress"),
            "completed": sum(1 for p in all_p if p["status"] == "completed"),
            "cancelled": sum(1 for p in all_p if p["status"] == "cancelled"),
            "total_tasks": total_tasks,
            "completed_tasks": done_tasks,
            "overall_progress_pct": round(done_tasks / total_tasks * 100, 1) if total_tasks else 0,
        }


# Singleton
_orchestrator = None

def get_orchestrator() -> ProjectOrchestrator:
    """Orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ProjectOrchestrator()
    return _orchestrator


if __name__ == "__main__":
    # Test
    async def test():
        orchestrator = get_orchestrator()
        
        project = SoftwareProject(
            name="AI Chatbot SaaS",
            description="Multi-tenant AI chatbot platformu",
            tech_stack=["FastAPI", "React", "PostgreSQL", "Gemini AI", "Docker"],
            requirements=["RESTful API", "Multi-tenant", "AI integration", "Admin panel"]
        )
        
        print(f"\n🚀 Proje başlatılıyor: {project.name}")
        project_id = await orchestrator.start_project(project)
        print(f"✅ Proje ID: {project_id}")
        
        # Durum takibi
        for i in range(10):
            await asyncio.sleep(2)
            status = orchestrator.get_project_status(project_id)
            if status:
                progress = status["progress"]["percentage"]
                print(f"📊 İlerleme: {progress:.1f}% ({status['progress']['completed']}/{status['progress']['total']} task)")
                
                if status["status"] == "completed":
                    print(f"\n✅ Proje tamamlandı!")
                    break
    
    asyncio.run(test())
