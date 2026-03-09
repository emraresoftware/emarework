"""
EmareUlak Entegrasyon Köprüsü
==============================

EmareUlak'tan gelen görevleri Hive Coordinator'a dağıtır.
100 proje için optimize edilmiş batch işlem desteği.
"""

from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import structlog

from src.services.coordination_engine import CoordinationEngine
from src.services.task_distributor import TaskDistributor
from src.models import TaskCreate, TaskPriority, TaskStatus

logger = structlog.get_logger()


class DistributionStrategy(str, Enum):
    """Görev dağıtım stratejisi"""
    WEIGHTED = "weighted"      # Yüke göre dağıt
    CASCADE = "cascade"        # Kademeli böl
    ROUND_ROBIN = "round-robin"  # Sırayla dağıt
    LEAST_LOADED = "least-loaded"  # En boş düğüme


@dataclass
class ProjectTask:
    """EmareUlak'tan gelen proje görevi"""
    project_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    estimated_kb: int = 30720  # 30 MB varsayılan
    deadline: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DistributionResult:
    """Dağıtım sonucu"""
    project_id: str
    task_uid: str
    assigned_to: str
    subtasks: List[str]
    status: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EmareUlakBridge:
    """
    EmareUlak ↔ Hive Coordinator köprüsü.
    
    EmareUlak'tan gelen projeleri Hive yapısına dağıtır ve
    durum güncellemelerini geri bildirir.
    """
    
    def __init__(
        self,
        engine: CoordinationEngine,
        task_distributor: TaskDistributor,
        strategy: DistributionStrategy = DistributionStrategy.WEIGHTED,
        auto_balance: bool = True,
    ):
        self.engine = engine
        self.task_dist = task_distributor
        self.strategy = strategy
        self.auto_balance = auto_balance
        self.projects: Dict[str, str] = {}  # project_id → task_uid
        
        logger.info("emareulak_bridge_initialized", strategy=strategy)
    
    async def distribute_project(
        self,
        project: ProjectTask,
    ) -> DistributionResult:
        """
        Tek bir projeyi dağıt.
        
        Args:
            project: Dağıtılacak proje
            
        Returns:
            DistributionResult: Dağıtım sonucu
        """
        try:
            # Öncelik dönüşümü
            priority_map = {
                "critical": TaskPriority.CRITICAL,
                "high": TaskPriority.HIGH,
                "medium": TaskPriority.MEDIUM,
                "low": TaskPriority.LOW,
            }
            priority = priority_map.get(project.priority, TaskPriority.MEDIUM)
            
            # Strateji seç
            if self.strategy == DistributionStrategy.WEIGHTED:
                strategy = "weighted"
                assigned_to = None  # Otomatik seçilecek
            elif self.strategy == DistributionStrategy.CASCADE:
                strategy = "cascade"
                assigned_to = "L0"  # Kökten başla
            elif self.strategy == DistributionStrategy.ROUND_ROBIN:
                strategy = "targeted"
                assigned_to = await self._round_robin_select()
            else:  # LEAST_LOADED
                strategy = "targeted"
                assigned_to = await self.engine.find_least_loaded_child("L0")
            
            # Görevi oluştur
            task = await self.task_dist.create_task(
                title=f"[EmareUlak] {project.title}",
                description=project.description,
                strategy=strategy,
                assigned_to=assigned_to or "L0",
                target_level=2,  # L2'ye kadar (100 düğüm)
                priority=priority,
                weight=project.estimated_kb // 1024,  # KB → MB
                deadline=project.deadline,
            )
            
            # Projeyi kaydet
            self.projects[project.project_id] = task.task_uid
            
            # Alt görevleri topla
            subtasks = task.subtask_uids if hasattr(task, 'subtask_uids') else []
            
            logger.info(
                "project_distributed",
                project_id=project.project_id,
                task_uid=task.task_uid,
                assigned_to=task.assigned_to,
                subtask_count=len(subtasks),
            )
            
            return DistributionResult(
                project_id=project.project_id,
                task_uid=task.task_uid,
                assigned_to=task.assigned_to,
                subtasks=subtasks,
                status="success",
                message=f"Proje başarıyla {task.assigned_to} adresine atandı",
            )
            
        except Exception as e:
            logger.error(
                "project_distribution_failed",
                project_id=project.project_id,
                error=str(e),
            )
            return DistributionResult(
                project_id=project.project_id,
                task_uid="",
                assigned_to="",
                subtasks=[],
                status="error",
                message=f"Dağıtım hatası: {str(e)}",
            )
    
    async def distribute_batch(
        self,
        projects: List[ProjectTask],
        parallel: bool = True,
    ) -> List[DistributionResult]:
        """
        Toplu proje dağıtımı (100 proje için optimize edilmiş).
        
        Args:
            projects: Dağıtılacak projeler
            parallel: Paralel dağıtım yapılsın mı
            
        Returns:
            List[DistributionResult]: Dağıtım sonuçları
        """
        logger.info("batch_distribution_started", project_count=len(projects))
        
        if parallel:
            # Paralel dağıtım (10'lu gruplar halinde)
            results = []
            batch_size = 10
            for i in range(0, len(projects), batch_size):
                batch = projects[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[self.distribute_project(p) for p in batch]
                )
                results.extend(batch_results)
                
                # Yük dengeleme kontrolü
                if self.auto_balance and i % 30 == 0:
                    await self.engine.rebalance_subtree("L0")
                    logger.info("auto_rebalance_triggered", processed=i)
        else:
            # Sıralı dağıtım
            results = []
            for project in projects:
                result = await self.distribute_project(project)
                results.append(result)
        
        # Özet istatistik
        success_count = sum(1 for r in results if r.status == "success")
        error_count = len(results) - success_count
        
        logger.info(
            "batch_distribution_completed",
            total=len(results),
            success=success_count,
            errors=error_count,
        )
        
        return results
    
    async def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Proje durumunu sorgula"""
        task_uid = self.projects.get(project_id)
        if not task_uid:
            return None
        
        # Görev durumunu task_distributor'ın belölçünden al
        task = self.task_dist.tasks.get(task_uid)
        if task:
            return {
                "project_id": project_id,
                "task_uid": task_uid,
                "status": task.status,
                "progress_pct": task.progress_pct,
                "assigned_to": task.assigned_to,
                "subtask_count": len(task.subtask_uids),
            }
        
        return {
            "project_id": project_id,
            "task_uid": task_uid,
            "status": "unknown",
            "progress_pct": 0,
        }
    
    async def get_all_projects_status(self) -> List[Dict[str, Any]]:
        """Tüm projelerin durumunu getir"""
        statuses = []
        for project_id in self.projects.keys():
            status = await self.get_project_status(project_id)
            if status:
                statuses.append(status)
        return statuses
    
    async def cancel_project(self, project_id: str) -> bool:
        """Projeyi iptal et"""
        task_uid = self.projects.get(project_id)
        if not task_uid:
            return False
        
        try:
            await self.task_dist.fail_task(task_uid, "EmareUlak tarafından iptal edildi")
            del self.projects[project_id]
            logger.info("project_cancelled", project_id=project_id)
            return True
        except Exception as e:
            logger.error("project_cancel_failed", project_id=project_id, error=str(e))
            return False
    
    async def _round_robin_select(self) -> str:
        """Round-robin düğüm seçimi"""
        # L1 düğümlerini döngüsel olarak seç
        current_index = len(self.projects) % 10
        return f"L1.{current_index}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri getir"""
        return {
            "total_projects": len(self.projects),
            "strategy": self.strategy,
            "auto_balance": self.auto_balance,
            "projects": list(self.projects.keys()),
        }
