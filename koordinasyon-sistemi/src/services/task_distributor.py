"""
Görev Dağıtım Sistemi
=====================

Görevleri hiyerarşi boyunca akıllıca dağıtır:

1. GÖREV OLUŞTURMA: Üst düğüm görev oluşturur
2. PARÇALAMA: Görev, hedef seviyeye kadar alt görevlere bölünür
3. ATAMA: Her alt görev en uygun düğüme atanır (yük dengeleme)
4. İZLEME: İlerleme aşağıdan yukarı toplanır
5. TAMAMLANMA: Tüm alt görevler bitince üst görev tamamlanır

Ölçek: Tek bir görev, 9 milyar alt göreve bölünebilir!
"""

from __future__ import annotations
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

from src import HIERARCHY_DEPTH, BRANCH_FACTOR
from src.utils.addressing import NodeAddress, format_node_count
from src.services.coordination_engine import CoordinationEngine

logger = structlog.get_logger()


@dataclass
class TaskNode:
    """Görev ağacındaki bir düğüm"""
    task_uid: str
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "pending"
    
    # Hiyerarşi
    parent_task_uid: Optional[str] = None
    assigned_to: Optional[str] = None  # Düğüm adresi
    created_by: str = "L0"
    target_level: int = HIERARCHY_DEPTH
    
    # Alt görevler
    subtask_uids: list[str] = field(default_factory=list)
    
    # Zamanlama
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # İlerleme
    progress_pct: float = 0.0
    weight: int = 10  # Görev ağırlığı (yük dengeleme için)
    
    # Meta
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    @property
    def is_leaf(self) -> bool:
        return len(self.subtask_uids) == 0
    
    @property
    def is_complete(self) -> bool:
        return self.status == "completed"
    
    @property
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline and self.status != "completed"


class TaskDistributor:
    """
    Görev dağıtım ve yönetim sistemi.
    
    Stratejiler:
    1. CASCADE: Görev aşağı doğru 10'a bölünür (varsayılan)
    2. TARGETED: Belirli bir düğüme doğrudan atama
    3. BROADCAST: Tüm alt ağaca aynı görev
    4. WEIGHTED: Yüke göre orantılı dağıtım
    """
    
    def __init__(self, engine: CoordinationEngine):
        self.engine = engine
        self.tasks: dict[str, TaskNode] = {}
        self._task_index_by_node: dict[str, list[str]] = {}  # address → task_uids
    
    # ─── Görev Oluşturma ────────────────────────────────────────────────
    
    async def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        created_by: str = "L0",
        assigned_to: Optional[str] = None,
        target_level: Optional[int] = None,
        deadline: Optional[datetime] = None,
        weight: int = 10,
        tags: list[str] = None,
        strategy: str = "cascade",
    ) -> TaskNode:
        """
        Yeni görev oluştur ve strateji'ye göre dağıt.
        
        strategy:
        - "cascade": Aşağı doğru otomatik parçala
        - "targeted": Sadece belirtilen düğüme ata
        - "broadcast": Alt ağacın her düğümüne kopyala
        - "weighted": Yüke göre orantılı dağıt
        """
        task = TaskNode(
            task_uid=f"T-{uuid.uuid4().hex[:12]}",
            title=title,
            description=description,
            priority=priority,
            created_by=created_by,
            assigned_to=assigned_to,
            target_level=target_level or HIERARCHY_DEPTH,
            deadline=deadline,
            weight=weight,
            tags=tags or [],
        )
        
        self.tasks[task.task_uid] = task
        
        # Düğüme atandıysa indeksle
        if assigned_to:
            self._index_task(assigned_to, task.task_uid)
        
        logger.info("görev_oluşturuldu", 
                    uid=task.task_uid, title=title, 
                    priority=priority, strategy=strategy)
        
        # Strateji'ye göre dağıt
        if strategy == "cascade" and assigned_to:
            await self._cascade_distribute(task)
        elif strategy == "broadcast" and assigned_to:
            await self._broadcast_distribute(task)
        elif strategy == "weighted" and assigned_to:
            await self._weighted_distribute(task)
        
        return task
    
    # ─── Dağıtım Stratejileri ───────────────────────────────────────────
    
    async def _cascade_distribute(self, task: TaskNode):
        """
        Kademeli dağıtım: Görev her seviyede 10'a bölünür.
        
        Örnek: "Web sitesi yap" görevi
        ├── L1.0: "Frontend modülü"
        │   ├── L2.0.0: "Ana sayfa"
        │   ├── L2.0.1: "İletişim sayfası"
        │   └── ...
        ├── L1.1: "Backend modülü"
        │   └── ...
        └── L1.2: "DevOps"
            └── ...
        """
        if not task.assigned_to:
            return
        
        assigned_addr = NodeAddress.from_string(task.assigned_to)
        
        # Hedef seviyeye ulaştıysa dağıtma
        if assigned_addr.level >= task.target_level:
            task.status = "assigned"
            return
        
        # Her çocuğa bir alt görev oluştur
        children = assigned_addr.children
        for i, child_addr in enumerate(children):
            child_str = child_addr.to_string()
            
            # Çocuk düğüm kayıtlı mı?
            if child_str not in self.engine.nodes:
                continue
            
            subtask = TaskNode(
                task_uid=f"T-{uuid.uuid4().hex[:12]}",
                title=f"{task.title} [Parça {i+1}/{BRANCH_FACTOR}]",
                description=task.description,
                priority=task.priority,
                parent_task_uid=task.task_uid,
                assigned_to=child_str,
                created_by=task.assigned_to,
                target_level=task.target_level,
                deadline=task.deadline,
                weight=max(1, task.weight // BRANCH_FACTOR),
                tags=task.tags,
            )
            
            self.tasks[subtask.task_uid] = subtask
            task.subtask_uids.append(subtask.task_uid)
            self._index_task(child_str, subtask.task_uid)
            
            # Rekursif dağıtım (bir sonraki seviye)
            await self._cascade_distribute(subtask)
        
        task.status = "in_progress"
        task.total_subtasks = len(task.subtask_uids)
    
    async def _weighted_distribute(self, task: TaskNode):
        """Yüke göre orantılı dağıtım"""
        if not task.assigned_to:
            return
        
        assigned_addr = NodeAddress.from_string(task.assigned_to)
        if assigned_addr.level >= task.target_level:
            task.status = "assigned"
            return
        
        # Çocukların yük durumuna göre ağırlık hesapla
        children_load = []
        total_available = 0
        
        for child_addr in assigned_addr.children:
            child_str = child_addr.to_string()
            if child_str in self.engine.nodes:
                node = self.engine.nodes[child_str]
                if node.is_available:
                    available = node.capacity - node.current_load
                    children_load.append((child_str, available))
                    total_available += available
        
        if total_available == 0:
            return
        
        # Orantılı dağıt
        for child_str, available in children_load:
            ratio = available / total_available
            sub_weight = max(1, int(task.weight * ratio))
            
            subtask = TaskNode(
                task_uid=f"T-{uuid.uuid4().hex[:12]}",
                title=f"{task.title} [Ağırlıklı Parça]",
                description=task.description,
                priority=task.priority,
                parent_task_uid=task.task_uid,
                assigned_to=child_str,
                created_by=task.assigned_to,
                target_level=task.target_level,
                weight=sub_weight,
            )
            
            self.tasks[subtask.task_uid] = subtask
            task.subtask_uids.append(subtask.task_uid)
            self._index_task(child_str, subtask.task_uid)
        
        task.status = "in_progress"
    
    async def _broadcast_distribute(self, task: TaskNode):
        """Tüm alt ağaca aynı görevi yayınla"""
        if not task.assigned_to:
            return
        
        assigned_addr = NodeAddress.from_string(task.assigned_to)
        if assigned_addr.level >= task.target_level:
            task.status = "assigned"
            return
        
        for child_addr in assigned_addr.children:
            child_str = child_addr.to_string()
            if child_str in self.engine.nodes:
                subtask = TaskNode(
                    task_uid=f"T-{uuid.uuid4().hex[:12]}",
                    title=task.title,  # Aynı başlık
                    description=task.description,
                    priority=task.priority,
                    parent_task_uid=task.task_uid,
                    assigned_to=child_str,
                    created_by=task.assigned_to,
                    target_level=task.target_level,
                )
                
                self.tasks[subtask.task_uid] = subtask
                task.subtask_uids.append(subtask.task_uid)
                self._index_task(child_str, subtask.task_uid)
                
                await self._broadcast_distribute(subtask)
        
        task.status = "in_progress"
    
    # ─── İlerleme Takibi ────────────────────────────────────────────────
    
    async def complete_task(self, task_uid: str) -> dict:
        """
        Bir görevi tamamla. Ebeveyn görevin ilerlemesini güncelle.
        Tüm kardeşler tamamlandıysa ebeveyn de tamamlanır.
        """
        if task_uid not in self.tasks:
            raise ValueError(f"Bilinmeyen görev: {task_uid}")
        
        task = self.tasks[task_uid]
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.progress_pct = 100.0
        
        # Atanan düğümün yükünü azalt
        if task.assigned_to and task.assigned_to in self.engine.nodes:
            node = self.engine.nodes[task.assigned_to]
            node.current_load = max(0, node.current_load - task.weight)
        
        logger.info("görev_tamamlandı", uid=task_uid)
        
        # Ebeveyn güncelle
        propagation = await self._propagate_completion(task_uid)
        
        return {
            "task_uid": task_uid,
            "status": "completed",
            "propagation": propagation,
        }
    
    async def _propagate_completion(self, task_uid: str) -> list[str]:
        """Tamamlanma bilgisini yukarı doğru yay"""
        task = self.tasks.get(task_uid)
        if not task or not task.parent_task_uid:
            return []
        
        parent = self.tasks.get(task.parent_task_uid)
        if not parent:
            return []
        
        propagated = []
        
        # Ebeveynin ilerlemesini güncelle
        completed_count = sum(
            1 for uid in parent.subtask_uids 
            if uid in self.tasks and self.tasks[uid].status == "completed"
        )
        total = len(parent.subtask_uids)
        
        if total > 0:
            parent.progress_pct = (completed_count / total) * 100
            parent.completed_subtasks = completed_count
        
        # Tüm alt görevler tamamlandıysa ebeveyni de tamamla
        if completed_count == total and total > 0:
            parent.status = "completed"
            parent.completed_at = datetime.utcnow()
            propagated.append(parent.task_uid)
            
            # Rekursif yukarı yay
            more = await self._propagate_completion(parent.task_uid)
            propagated.extend(more)
        
        return propagated
    
    async def fail_task(self, task_uid: str, reason: str = ""):
        """Bir görevi başarısız olarak işaretle"""
        if task_uid not in self.tasks:
            raise ValueError(f"Bilinmeyen görev: {task_uid}")
        
        task = self.tasks[task_uid]
        task.status = "failed"
        task.metadata["failure_reason"] = reason
        
        logger.warning("görev_başarısız", uid=task_uid, reason=reason)
        
        # Üste eskale et
        if task.parent_task_uid:
            parent = self.tasks.get(task.parent_task_uid)
            if parent:
                parent.status = "blocked"
                parent.metadata.setdefault("blocked_by", []).append(task_uid)
    
    # ─── Sorgular ───────────────────────────────────────────────────────
    
    def get_node_tasks(self, address: str) -> list[TaskNode]:
        """Bir düğüme atanan tüm görevler"""
        task_uids = self._task_index_by_node.get(address, [])
        return [self.tasks[uid] for uid in task_uids if uid in self.tasks]
    
    def get_task_tree(self, task_uid: str, max_depth: int = 3) -> dict:
        """Bir görevin alt görev ağacını getir"""
        task = self.tasks.get(task_uid)
        if not task:
            return {}
        
        result = {
            "uid": task.task_uid,
            "title": task.title,
            "status": task.status,
            "assigned_to": task.assigned_to,
            "progress_pct": task.progress_pct,
            "subtasks": [],
        }
        
        if max_depth > 0:
            for sub_uid in task.subtask_uids:
                sub_tree = self.get_task_tree(sub_uid, max_depth - 1)
                if sub_tree:
                    result["subtasks"].append(sub_tree)
        
        return result
    
    def get_statistics(self) -> dict:
        """Görev sistemi istatistikleri"""
        total = len(self.tasks)
        by_status = {}
        by_priority = {}
        
        for task in self.tasks.values():
            by_status[task.status] = by_status.get(task.status, 0) + 1
            by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
        
        overdue = sum(1 for t in self.tasks.values() if t.is_overdue)
        
        return {
            "total_tasks": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue_tasks": overdue,
        }
    
    # ─── Yardımcı ───────────────────────────────────────────────────────
    
    def _index_task(self, address: str, task_uid: str):
        """Görev-düğüm indeksini güncelle"""
        if address not in self._task_index_by_node:
            self._task_index_by_node[address] = []
        self._task_index_by_node[address].append(task_uid)
