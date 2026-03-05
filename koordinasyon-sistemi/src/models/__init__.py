"""
Veritabanı Modelleri - Hiyerarşik Düğüm Yapısı
================================================

9 milyar düğüm için verimli depolama:
- Düğüm kimliği: Seviye tabanlı adres sistemi (ör: "0.3.7.2.1.0.4.8.9.5")
- Materialized Path: Hızlı alt ağaç sorguları
- Adjacency List: Doğrudan ebeveyn-çocuk ilişkileri
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, DateTime, Text,
    ForeignKey, Index, Enum as SQLEnum, JSON, Boolean,
    create_engine
)
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()


# ─── Enum Tanımları ─────────────────────────────────────────────────────────

class NodeStatus(str, Enum):
    ACTIVE = "active"            # Çalışıyor
    IDLE = "idle"                # Boşta
    BUSY = "busy"                # Meşgul
    OFFLINE = "offline"          # Çevrimdışı
    MAINTENANCE = "maintenance"  # Bakımda


class TaskStatus(str, Enum):
    PENDING = "pending"          # Bekliyor
    ASSIGNED = "assigned"        # Atandı
    IN_PROGRESS = "in_progress"  # Devam ediyor
    REVIEW = "review"            # İncelemede
    COMPLETED = "completed"      # Tamamlandı
    FAILED = "failed"            # Başarısız
    BLOCKED = "blocked"          # Engellendi


class TaskPriority(str, Enum):
    CRITICAL = "critical"    # P0 - Acil
    HIGH = "high"            # P1 - Yüksek
    MEDIUM = "medium"        # P2 - Orta
    LOW = "low"              # P3 - Düşük


class MessageType(str, Enum):
    DIRECTIVE = "directive"      # Yukarıdan aşağı emir
    REPORT = "report"            # Aşağıdan yukarı rapor
    BROADCAST = "broadcast"      # Tüm alt ağaca yayın
    PEER = "peer"                # Aynı seviye iletişim
    ESCALATION = "escalation"    # Üst seviyeye iletim


# ─── Veritabanı Tabloları ───────────────────────────────────────────────────

class Node(Base):
    """
    Hiyerarşideki bir düğüm (yazılımcı/takım lideri).
    
    Adres Şeması: "L{seviye}.{dal_index_dizisi}"
    Örnek: "L3.0.4.7" → Seviye 3, kök→dal0→dal4→dal7
    
    9 milyar düğümü verimli sorgulamak için materialized path kullanılır.
    """
    __tablename__ = "nodes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    address = Column(String(64), unique=True, nullable=False, index=True)
    # Materialized path: "0/3/7/2/1" gibi - alt ağaç sorguları için
    path = Column(String(128), nullable=False, index=True)
    level = Column(Integer, nullable=False, index=True)
    parent_address = Column(String(64), ForeignKey("nodes.address"), nullable=True)
    
    # Düğüm bilgileri
    name = Column(String(256), nullable=True)
    role = Column(String(128), nullable=True)
    status = Column(SQLEnum(NodeStatus), default=NodeStatus.ACTIVE, index=True)
    
    # Kapasite metrikleri
    capacity = Column(Integer, default=100)          # Maks iş yükü puanı
    current_load = Column(Integer, default=0)          # Mevcut yük
    efficiency_score = Column(Float, default=1.0)      # Verimlilik katsayısı (0-2)
    
    # Alt ağaç toplu metrikleri (yukarı toplanan)
    subtree_total_nodes = Column(BigInteger, default=1)
    subtree_active_nodes = Column(BigInteger, default=1)
    subtree_tasks_completed = Column(BigInteger, default=0)
    subtree_avg_efficiency = Column(Float, default=1.0)
    
    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Meta veri
    metadata_json = Column(JSON, default=dict)

    __table_args__ = (
        Index("ix_nodes_level_status", "level", "status"),
        Index("ix_nodes_path_prefix", "path"),  # PREFIX aramaları için
        Index("ix_nodes_parent", "parent_address"),
        Index("ix_nodes_load", "current_load", "capacity"),
    )


class Task(Base):
    """
    Görev - yukarıdan aşağı akan iş birimleri.
    
    Bir görev oluşturulduğunda hiyerarşi boyunca aşağı parçalanır.
    Her alt görev, üst görevin bir parçasıdır.
    """
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_uid = Column(String(64), unique=True, nullable=False, index=True)
    parent_task_uid = Column(String(64), ForeignKey("tasks.task_uid"), nullable=True)
    
    # Görev bilgileri
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # Atama
    assigned_to = Column(String(64), ForeignKey("nodes.address"), nullable=True, index=True)
    created_by = Column(String(64), ForeignKey("nodes.address"), nullable=False)
    target_level = Column(Integer, nullable=True)  # Hangi seviyeye kadar parçalanacak
    
    # Zamanlama
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Parçalanma metrikleri
    total_subtasks = Column(BigInteger, default=0)
    completed_subtasks = Column(BigInteger, default=0)
    progress_pct = Column(Float, default=0.0)
    
    # Meta
    tags = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)

    __table_args__ = (
        Index("ix_tasks_status_priority", "status", "priority"),
        Index("ix_tasks_assigned_status", "assigned_to", "status"),
        Index("ix_tasks_parent", "parent_task_uid"),
    )


class Message(Base):
    """
    Kademeli mesajlaşma sistemi.
    
    Mesajlar hiyerarşi boyunca yayılır:
    - DIRECTIVE: Üstten alta doğru
    - REPORT: Alttan üste doğru (toplu)
    - BROADCAST: Bir düğümden tüm alt ağacına
    - ESCALATION: Bir sorun üste iletilir
    """
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_uid = Column(String(64), unique=True, nullable=False, index=True)
    message_type = Column(SQLEnum(MessageType), nullable=False, index=True)
    
    sender_address = Column(String(64), ForeignKey("nodes.address"), nullable=False)
    recipient_address = Column(String(64), ForeignKey("nodes.address"), nullable=True)
    broadcast_path = Column(String(128), nullable=True)  # Yayın hedef path
    
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=True)
    
    # Kademeli yayın durumu
    cascade_depth = Column(Integer, default=0)     # Kaç seviye yayıldı
    cascade_target = Column(Integer, nullable=True) # Hedef yayılma seviyesi
    cascade_reached = Column(BigInteger, default=0)  # Ulaşılan düğüm sayısı
    
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    metadata_json = Column(JSON, default=dict)

    __table_args__ = (
        Index("ix_messages_recipient", "recipient_address", "is_read"),
        Index("ix_messages_type_time", "message_type", "created_at"),
    )


class AggregatedMetrics(Base):
    """
    Periyodik olarak toplanan metrikler.
    Her düğüm kendi alt ağacının metriklerini yukarı toplar.
    """
    __tablename__ = "aggregated_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    node_address = Column(String(64), ForeignKey("nodes.address"), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Performans
    tasks_created = Column(BigInteger, default=0)
    tasks_completed = Column(BigInteger, default=0)
    tasks_failed = Column(BigInteger, default=0)
    avg_completion_time_hours = Column(Float, default=0.0)
    
    # Kaynak kullanımı
    active_nodes = Column(BigInteger, default=0)
    idle_nodes = Column(BigInteger, default=0)
    offline_nodes = Column(BigInteger, default=0)
    avg_load_pct = Column(Float, default=0.0)
    
    # İletişim
    messages_sent = Column(BigInteger, default=0)
    escalations = Column(BigInteger, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_metrics_node_period", "node_address", "period_start"),
    )


# ─── Pydantic Şemaları (API için) ───────────────────────────────────────────

class NodeCreate(BaseModel):
    address: str = Field(..., description="Düğüm adresi: 'L{seviye}.{indeksler}'")
    name: Optional[str] = None
    role: Optional[str] = None
    parent_address: Optional[str] = None

class NodeResponse(BaseModel):
    address: str
    path: str
    level: int
    name: Optional[str]
    role: Optional[str]
    status: NodeStatus
    capacity: int
    current_load: int
    efficiency_score: float
    subtree_total_nodes: int
    subtree_active_nodes: int
    subtree_tasks_completed: int
    subtree_avg_efficiency: float
    last_heartbeat: datetime
    
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    created_by: str
    assigned_to: Optional[str] = None
    target_level: Optional[int] = None
    deadline: Optional[datetime] = None
    tags: list[str] = []

class TaskResponse(BaseModel):
    task_uid: str
    title: str
    priority: TaskPriority
    status: TaskStatus
    assigned_to: Optional[str]
    created_by: str
    progress_pct: float
    total_subtasks: int
    completed_subtasks: int
    created_at: datetime
    deadline: Optional[datetime]
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    message_type: MessageType
    sender_address: str
    recipient_address: Optional[str] = None
    broadcast_path: Optional[str] = None
    subject: str
    body: Optional[str] = None
    cascade_target: Optional[int] = None

class SubtreeStats(BaseModel):
    """Bir alt ağacın toplu istatistikleri"""
    root_address: str
    total_nodes: int
    active_nodes: int
    idle_nodes: int
    offline_nodes: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    failed_tasks: int
    avg_efficiency: float
    avg_load_pct: float
    health_score: float  # 0-100 arası genel sağlık puanı
