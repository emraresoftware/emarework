"""
Repository Pattern - Database access layer
Clean separation from business logic
"""
from typing import Optional, List, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import structlog

from .models import Node, Task, Message, SubtreeMetrics

logger = structlog.get_logger()


class NodeRepository:
    """Düğüm veritabanı işlemleri"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, **kwargs: Any) -> Node:
        """Yeni düğüm oluştur"""
        node = Node(**kwargs)
        self.db.add(node)
        await self.db.flush()
        await self.db.refresh(node)
        logger.info("node_created", address=node.address, level=node.level)
        return node
    
    async def get_by_address(self, address: str) -> Optional[Node]:
        """Adrese göre düğüm getir"""
        result = await self.db.execute(
            select(Node).where(Node.address == address)
        )
        return result.scalar_one_or_none()
    
    async def get_by_level(self, level: int) -> List[Node]:
        """Seviyeye göre tüm düğümleri getir"""
        result = await self.db.execute(
            select(Node).where(Node.level == level)
        )
        return list(result.scalars().all())
    
    async def get_children(self, parent_address: str) -> List[Node]:
        """Alt düğümleri getir"""
        # L1.3 → L2.3.0, L2.3.1, ..., L2.3.9
        pattern = f"{parent_address}.%"
        result = await self.db.execute(
            select(Node).where(Node.address.like(pattern))
        )
        return list(result.scalars().all())
    
    async def update_load(self, address: str, new_load: int) -> None:
        """Düğüm yükünü güncelle"""
        await self.db.execute(
            update(Node)
            .where(Node.address == address)
            .values(current_load=new_load, updated_at=datetime.now(timezone.utc))
        )
    
    async def update_heartbeat(self, address: str) -> None:
        """Heartbeat zamanını güncelle"""
        await self.db.execute(
            update(Node)
            .where(Node.address == address)
            .values(last_heartbeat=datetime.now(timezone.utc), status="active")
        )
    
    async def get_least_loaded(self, level: int, limit: int = 10) -> List[Node]:
        """En az yüklü düğümleri getir"""
        result = await self.db.execute(
            select(Node)
            .where(Node.level == level, Node.status == "active")
            .order_by(Node.current_load.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_level(self, level: int) -> int:
        """Seviyedeki düğüm sayısı"""
        result = await self.db.execute(
            select(Node).where(Node.level == level)
        )
        return len(list(result.scalars().all()))
    
    async def delete_node(self, address: str) -> None:
        """Düğümü sil"""
        await self.db.execute(
            delete(Node).where(Node.address == address)
        )


class TaskRepository:
    """Görev veritabanı işlemleri"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, **kwargs: Any) -> Task:
        """Yeni görev oluştur"""
        task = Task(**kwargs)
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        logger.info("task_created", task_uid=task.task_uid, assigned_to=task.assigned_to)
        return task
    
    async def get_by_uid(self, task_uid: str) -> Optional[Task]:
        """UID'ye göre görev getir"""
        result = await self.db.execute(
            select(Task).where(Task.task_uid == task_uid)
        )
        return result.scalar_one_or_none()
    
    async def get_by_node(self, node_address: str, status: Optional[str] = None) -> List[Task]:
        """Düğüme atanmış görevleri getir"""
        query = select(Task).where(Task.assigned_to == node_address)
        if status:
            query = query.where(Task.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_status(
        self, 
        task_uid: str, 
        status: str, 
        progress: Optional[float] = None,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Görev durumunu güncelle"""
        values: dict[str, Any] = {"status": status, "updated_at": datetime.now(timezone.utc)}
        
        if progress is not None:
            values["progress"] = progress
        
        if result is not None:
            values["result"] = result
        
        if error is not None:
            values["error"] = error
        
        if status == "in_progress" and not await self._get_started_at(task_uid):
            values["started_at"] = datetime.now(timezone.utc)
        
        if status in ("completed", "failed"):
            values["completed_at"] = datetime.now(timezone.utc)
            # Süreyi hesapla
            started = await self._get_started_at(task_uid)
            if started:
                from datetime import timezone
                values["actual_duration_sec"] = int(
                    (datetime.now(timezone.utc) - started.replace(tzinfo=timezone.utc)).total_seconds()
                )
        
        await self.db.execute(
            update(Task).where(Task.task_uid == task_uid).values(**values)
        )
    
    async def _get_started_at(self, task_uid: str) -> Optional[datetime]:
        """Görevin başlama zamanını al"""
        result = await self.db.execute(
            select(Task.started_at).where(Task.task_uid == task_uid)
        )
        return result.scalar_one_or_none()
    
    async def get_subtasks(self, parent_task_id: int) -> List[Task]:
        """Alt görevleri getir"""
        result = await self.db.execute(
            select(Task).where(Task.parent_task_id == parent_task_id)
        )
        return list(result.scalars().all())
    
    async def count_by_status(self, status: str) -> int:
        """Duruma göre görev sayısı"""
        result = await self.db.execute(
            select(Task).where(Task.status == status)
        )
        return len(list(result.scalars().all()))


class MessageRepository:
    """Mesaj veritabanı işlemleri"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, **kwargs: Any) -> Message:
        """Yeni mesaj oluştur"""
        message = Message(**kwargs)
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        logger.info("message_created", 
                   message_uid=message.message_uid, 
                   type=message.message_type,
                   sender=message.sender_address,
                   recipient=message.recipient_address)
        return message
    
    async def get_by_uid(self, message_uid: str) -> Optional[Message]:
        """UID'ye göre mesaj getir"""
        result = await self.db.execute(
            select(Message).where(Message.message_uid == message_uid)
        )
        return result.scalar_one_or_none()
    
    async def get_inbox(self, node_address: str, unread_only: bool = False) -> List[Message]:
        """Gelen kutusu"""
        query = select(Message).where(Message.recipient_address == node_address)
        if unread_only:
            query = query.where(Message.status != "read")
        result = await self.db.execute(query.order_by(Message.created_at.desc()))
        return list(result.scalars().all())
    
    async def mark_delivered(self, message_uid: str) -> None:
        """Mesajı teslim edildi olarak işaretle"""
        await self.db.execute(
            update(Message)
            .where(Message.message_uid == message_uid)
            .values(status="delivered", delivered_at=datetime.now(timezone.utc))
        )
    
    async def mark_read(self, message_uid: str) -> None:
        """Mesajı okundu olarak işaretle"""
        await self.db.execute(
            update(Message)
            .where(Message.message_uid == message_uid)
            .values(status="read", read_at=datetime.now(timezone.utc))
        )
    
    async def increment_retry(self, message_uid: str) -> None:
        """Retry sayacını artır"""
        await self.db.execute(
            update(Message)
            .where(Message.message_uid == message_uid)
            .values(retry_count=Message.retry_count + 1)
        )


class MetricsRepository:
    """Alt ağaç metrikleri işlemleri"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upsert(self, node_address: str, **metrics: Any) -> SubtreeMetrics:
        """Metrikleri create veya update et"""
        result = await self.db.execute(
            select(SubtreeMetrics).where(SubtreeMetrics.node_address == node_address)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await self.db.execute(
                update(SubtreeMetrics)
                .where(SubtreeMetrics.node_address == node_address)
                .values(**metrics, last_aggregated_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            )
            await self.db.refresh(existing)
            return existing
        else:
            new_metrics = SubtreeMetrics(node_address=node_address, **metrics)
            self.db.add(new_metrics)
            await self.db.flush()
            await self.db.refresh(new_metrics)
            return new_metrics
    
    async def get(self, node_address: str) -> Optional[SubtreeMetrics]:
        """Metrik getir"""
        result = await self.db.execute(
            select(SubtreeMetrics).where(SubtreeMetrics.node_address == node_address)
        )
        return result.scalar_one_or_none()
    
    async def mark_stale(self, node_address: str) -> None:
        """Metriği bayat olarak işaretle (yeniden hesaplanmalı)"""
        await self.db.execute(
            update(SubtreeMetrics)
            .where(SubtreeMetrics.node_address == node_address)
            .values(is_stale=True)
        )
