"""
SQLAlchemy Veritabanı Modelleri
Production-ready: indexes, relationships, validators
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore
from datetime import datetime, timezone
from .database import Base

def utcnow():
    """UTC now with timezone awareness"""
    return datetime.now(timezone.utc)


class Node(Base):
    """
    Hiyerarşik düğüm modeli - her düğüm bir koordinatör
    """
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(100), unique=True, nullable=False, index=True)  # L0, L1.3, L2.0.5
    name = Column(String(255), nullable=True)
    level = Column(Integer, nullable=False, index=True)
    
    # Durum
    status = Column(String(20), default="active", index=True)  # active, idle, busy, offline, maintenance
    capacity = Column(Integer, default=100)
    current_load = Column(Integer, default=0)
    efficiency = Column(Float, default=1.0)
    
    # Heartbeat
    last_heartbeat = Column(DateTime, default=utcnow, nullable=False)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Ek bilgiler
    
    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # İlişkiler
    tasks = relationship("Task", back_populates="assigned_node", foreign_keys="Task.assigned_to")
    sent_messages = relationship("Message", back_populates="sender_node", foreign_keys="Message.sender_address")
    received_messages = relationship("Message", back_populates="recipient_node", foreign_keys="Message.recipient_address")
    
    @property
    def load_pct(self) -> float:
        """Yük yüzdesi"""
        if self.capacity == 0:  # type: ignore
            return 100.0
        return (self.current_load / self.capacity) * 100.0  # type: ignore
    
    @property
    def is_available(self) -> bool:
        """Düğüm müsait mi?"""
        return self.status == "active" and self.load_pct < 90.0  # type: ignore
    
    def __repr__(self):
        return f"<Node {self.address} ({self.status})>"


class Task(Base):
    """
    Görev modeli - düğümlere atanan işler
    """
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_uid = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    
    # Görev bilgileri
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    
    # Atama
    assigned_to = Column(String(100), ForeignKey("nodes.address"), nullable=False, index=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Durum
    status = Column(String(20), default="pending", index=True)  # pending, assigned, in_progress, completed, failed
    priority = Column(String(10), default="medium")  # low, medium, high, critical
    progress = Column(Float, default=0.0)  # 0-100
    
    # Ağırlık ve kaynaklar
    weight = Column(Integer, default=1)  # Görev ağırlığı (MB, birim, vb.)
    estimated_duration_sec = Column(Integer, nullable=True)
    actual_duration_sec = Column(Integer, nullable=True)
    
    # Strategi
    strategy = Column(String(20), nullable=True)  # cascade, weighted, broadcast, targeted
    target_level = Column(Integer, nullable=True)
    
    # Zaman
    deadline = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # İlişkiler
    assigned_node = relationship("Node", back_populates="tasks", foreign_keys=[assigned_to])
    parent_task = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task", foreign_keys=[parent_task_id])
    
    def __repr__(self):
        return f"<Task {self.task_uid[:8]} → {self.assigned_to} ({self.status})>"


class Message(Base):
    """
    Mesaj modeli - düğümler arası iletişim
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_uid = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    
    # Gönderici ve alıcı
    sender_address = Column(String(100), ForeignKey("nodes.address"), nullable=False)
    recipient_address = Column(String(100), ForeignKey("nodes.address"), nullable=False, index=True)
    
    # Mesaj içeriği
    message_type = Column(String(20), nullable=False)  # directive, report, broadcast, peer, escalation
    subject = Column(String(512), nullable=True)
    body = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    
    # Durum
    status = Column(String(20), default="pending")  # pending, delivered, read, failed
    priority = Column(String(10), default="medium")
    
    # Zaman
    ttl_sec = Column(Integer, default=3600)
    expires_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Retry
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # İlişkiler
    sender_node = relationship("Node", back_populates="sent_messages", foreign_keys=[sender_address])
    recipient_node = relationship("Node", back_populates="received_messages", foreign_keys=[recipient_address])
    
    def __repr__(self):
        return f"<Message {self.message_type} {self.sender_address}→{self.recipient_address}>"


class SubtreeMetrics(Base):
    """
    Alt ağaç metrikleri - cache tablosu (aggregation sonuçları)
    """
    __tablename__ = "subtree_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    node_address = Column(String(100), ForeignKey("nodes.address"), nullable=False, unique=True, index=True)
    
    # Metrikler
    total_descendants = Column(Integer, default=0)
    active_descendants = Column(Integer, default=0)
    total_load = Column(Integer, default=0)
    total_capacity = Column(Integer, default=0)
    avg_efficiency = Column(Float, default=1.0)
    
    # Görev istatistikleri
    pending_tasks = Column(Integer, default=0)
    in_progress_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Cache metadata
    last_aggregated_at = Column(DateTime, default=utcnow, nullable=False)
    is_stale = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SubtreeMetrics {self.node_address} ({self.total_descendants} nodes)>"
