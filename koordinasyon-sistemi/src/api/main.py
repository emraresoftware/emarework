"""
REST API - Hive Coordinator Dashboard
======================================

FastAPI tabanlı izleme ve yönetim API'si.
Tüm hiyerarşiyi web üzerinden yönetmeye olanak tanır.
"""

from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import os

from src import __version__, HIERARCHY_DEPTH, BRANCH_FACTOR, settings
from src.utils.addressing import NodeAddress, level_summary, format_node_count
from src.services.coordination_engine import CoordinationEngine
from src.services.task_distributor import TaskDistributor
from src.services.message_cascade import MessageCascade
from src.emareulak_bridge import EmareUlakBridge, ProjectTask, DistributionStrategy
from src.models import (
    NodeCreate, NodeResponse, TaskCreate, TaskResponse,
    MessageCreate, SubtreeStats, TaskPriority, TaskStatus
)
from src.db import init_db, close_db, get_db
from src.emare_workers import get_workforce
from src.project_splitter import SoftwareProject, ProjectSplitter
from src.project_orchestrator import get_orchestrator
from src.emare_ecosystem import get_ecosystem
from src.dergah_sohbet import get_dergah
from src.dervish_capabilities import get_capabilities, get_all_capabilities, get_capabilities_summary
from pydantic import BaseModel
from typing import List
import structlog

logger = structlog.get_logger()

# ─── Uygulama Başlatma ──────────────────────────────────────────────────────

engine = CoordinationEngine()
task_dist = TaskDistributor(engine)
msg_cascade = MessageCascade(engine)
emareulak = EmareUlakBridge(engine, task_dist, strategy=DistributionStrategy.WEIGHTED)

# Emare AI Workers
workforce = get_workforce()
orchestrator = get_orchestrator()

# Emare Ekosistem Yöneticisi
ecosystem = get_ecosystem()
project_splitter = ProjectSplitter()

# Dergah Sohbet Odası
dergah = get_dergah()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü - başlatma/kapatma"""
    logger.info("app_startup", version=__version__)
    
    # Database başlat
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
    
    # Kök düğümü oluştur (memory-based engine için)
    await engine.register_node("L0", name="Genel Koordinatör")
    
    # Servisleri birbirine bağla (entegrasyon)
    engine.set_message_cascade(msg_cascade)
    engine.set_task_distributor(task_dist)
    
    yield
    
    # Cleanup
    logger.info("app_shutdown")
    try:
        await close_db()
        logger.info("database_closed")
    except Exception as e:
        logger.error("database_close_failed", error=str(e))

app = FastAPI(
    title="Emare Work - Koordinasyon Sistemi",
    description=f"""
    🚀 Emare Work - 9 Milyar Düğümlü Yazılım Ekibi Koordinasyon Sistemi
    
    - **Hiyerarşi Derinliği**: {HIERARCHY_DEPTH} seviye
    - **Dallanma Faktörü**: {BRANCH_FACTOR} çocuk/düğüm
    - **Teorik Maksimum**: ~{format_node_count(sum(10**i for i in range(11)))} düğüm
    
    **Kullanım Kolaylığı**: Web tabanlı, kullanıcı dostu arayüz
    """,
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ═══════════════════════════════════════════════════════════════════════════════
# GENEL BİLGİ
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse, tags=["Genel"], include_in_schema=False)
async def root_html():
    """Ana sayfa - Dashboard UI"""
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    # Fallback to JSON if HTML doesn't exist
    return await root_api()

@app.get("/control-panel", response_class=HTMLResponse, tags=["Genel"], include_in_schema=False)
async def control_panel():
    """Proje dağıtım kontrol paneli"""
    html_path = os.path.join(static_dir, "control-panel.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Kontrol paneli bulunamadı")

@app.get("/dashboard", response_class=HTMLResponse, tags=["Genel"], include_in_schema=False)
async def advanced_dashboard():
    """Gelişmiş dashboard - Analytics, AI worker management, real-time monitoring"""
    html_path = os.path.join(static_dir, "advanced-dashboard.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="Dashboard bulunamadı")

@app.get("/api", tags=["Genel"])
async def root_api():
    """Sistem genel durumu (JSON API)"""
    return {
        "system": "Emare Work",
        "version": __version__,
        "status": "operational",
        "hierarchy": {
            "depth": HIERARCHY_DEPTH,
            "branch_factor": BRANCH_FACTOR,
            "theoretical_capacity": format_node_count(sum(10**i for i in range(11))),
        },
        "overview": engine.get_system_overview(),
    }

@app.get("/health", tags=["Genel"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Sağlık kontrolü endpoint'i - Docker healthcheck için
    Database, Redis ve uygulama durumunu kontrol eder
    """
    from src.cache import _get_redis_client
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__,
        "checks": {}
    }
    
    # Database kontrolü
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis kontrolü
    try:
        client = await _get_redis_client()
        if client:
            await client.ping()
            await client.aclose()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "disabled"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Uygulama durumu
    health_status["checks"]["app"] = "ok"
    health_status["checks"]["nodes_count"] = len(engine.nodes)
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/hierarchy", tags=["Genel"])
async def get_hierarchy_summary():
    """Hiyerarşi seviye özeti"""
    return level_summary()


# ═══════════════════════════════════════════════════════════════════════════════
# DÜĞÜM YÖNETİMİ
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/nodes", tags=["Düğümler"])
async def register_node(node_data: NodeCreate):
    """Yeni düğüm kaydet"""
    try:
        node = await engine.register_node(
            address=node_data.address,
            name=node_data.name,
        )
        return {
            "status": "created",
            "address": node.address.to_string(),
            "level": node.address.level,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/nodes/{address}", tags=["Düğümler"])
async def get_node(address: str):
    """Düğüm bilgisini getir"""
    if address not in engine.nodes:
        raise HTTPException(status_code=404, detail=f"Düğüm bulunamadı: {address}")
    
    node = engine.nodes[address]
    return {
        "address": node.address.to_string(),
        "level": node.address.level,
        "status": node.status,
        "capacity": node.capacity,
        "current_load": node.current_load,
        "load_pct": node.load_pct,
        "efficiency": node.efficiency,
        "is_healthy": node.is_healthy,
        "last_heartbeat": node.last_heartbeat.isoformat(),
        "subtree_size": node.address.subtree_size,
        "subtree_size_str": format_node_count(node.address.subtree_size),
    }

@app.get("/nodes/{address}/children", tags=["Düğümler"])
async def get_node_children(address: str):
    """Düğümün çocuklarını getir"""
    node_addr = NodeAddress.from_string(address)
    children = []
    
    for child_addr in node_addr.children:
        child_str = child_addr.to_string()
        if child_str in engine.nodes:
            child = engine.nodes[child_str]
            children.append({
                "address": child_str,
                "status": child.status,
                "load_pct": child.load_pct,
                "efficiency": child.efficiency,
            })
    
    return {
        "parent": address,
        "children_count": len(children),
        "children": children,
    }

@app.post("/nodes/{address}/heartbeat", tags=["Düğümler"])
async def node_heartbeat(address: str):
    """Düğüm heartbeat"""
    try:
        result = await engine.heartbeat(address)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/nodes/{address}/status", tags=["Düğümler"])
async def update_node_status(address: str, status: str, load: int = None):
    """Düğüm durumunu güncelle"""
    try:
        await engine.update_node_status(address, status, load)
        return {"status": "updated", "address": address, "new_status": status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# GÖREV YÖNETİMİ
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/tasks", tags=["Görevler"])
async def create_task(task_data: TaskCreate):
    """Yeni görev oluştur ve dağıt"""
    task = await task_dist.create_task(
        title=task_data.title,
        description=task_data.description or "",
        priority=task_data.priority.value,
        created_by=task_data.created_by,
        assigned_to=task_data.assigned_to,
        target_level=task_data.target_level,
        deadline=task_data.deadline,
        tags=task_data.tags,
    )
    
    return {
        "task_uid": task.task_uid,
        "title": task.title,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "subtasks_created": len(task.subtask_uids),
    }

@app.get("/tasks/{task_uid}", tags=["Görevler"])
async def get_task(task_uid: str):
    """Görev detayı"""
    task = task_dist.tasks.get(task_uid)
    if not task:
        raise HTTPException(status_code=404, detail=f"Görev bulunamadı: {task_uid}")
    
    return {
        "task_uid": task.task_uid,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assigned_to": task.assigned_to,
        "created_by": task.created_by,
        "progress_pct": task.progress_pct,
        "subtask_count": len(task.subtask_uids),
        "created_at": task.created_at.isoformat(),
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "is_overdue": task.is_overdue,
    }

@app.get("/tasks/{task_uid}/tree", tags=["Görevler"])
async def get_task_tree(task_uid: str, depth: int = 3):
    """Görev ağacını getir"""
    tree = task_dist.get_task_tree(task_uid, max_depth=depth)
    if not tree:
        raise HTTPException(status_code=404, detail=f"Görev bulunamadı: {task_uid}")
    return tree

@app.post("/tasks/{task_uid}/complete", tags=["Görevler"])
async def complete_task(task_uid: str):
    """Görevi tamamla"""
    try:
        result = await task_dist.complete_task(task_uid)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/tasks/{task_uid}/fail", tags=["Görevler"])
async def fail_task(task_uid: str, reason: str = ""):
    """Görevi başarısız işaretle"""
    try:
        await task_dist.fail_task(task_uid, reason)
        return {"task_uid": task_uid, "status": "failed", "reason": reason}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/nodes/{address}/tasks", tags=["Görevler"])
async def get_node_tasks(address: str):
    """Düğüme atanan görevler"""
    tasks = task_dist.get_node_tasks(address)
    return {
        "address": address,
        "task_count": len(tasks),
        "tasks": [
            {
                "uid": t.task_uid,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "progress_pct": t.progress_pct,
            }
            for t in tasks
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MESAJLAŞMA
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/messages/directive", tags=["Mesajlar"])
async def send_directive(
    sender: str,
    subject: str,
    body: str = "",
    target_depth: int = 1,
    priority: str = "medium",
):
    """Yukarıdan aşağı emir gönder"""
    msg = await msg_cascade.send_directive(
        sender=sender,
        subject=subject,
        body=body,
        target_depth=target_depth,
        priority=priority,
    )
    return {
        "message_uid": msg.message_uid,
        "type": "directive",
        "cascade_reached": msg.cascade_reached,
        "cascade_depth": msg.cascade_depth,
    }

@app.post("/messages/broadcast", tags=["Mesajlar"])
async def send_broadcast(sender: str, subject: str, body: str = ""):
    """Tüm alt ağaca yayın"""
    msg = await msg_cascade.send_broadcast(sender=sender, subject=subject, body=body)
    return {
        "message_uid": msg.message_uid,
        "type": "broadcast",
        "cascade_reached": msg.cascade_reached,
    }

@app.post("/messages/report", tags=["Mesajlar"])
async def send_report(
    sender: str,
    subject: str,
    body: str = "",
    escalate: bool = False,
):
    """Aşağıdan yukarı rapor gönder"""
    msg = await msg_cascade.send_report(
        sender=sender,
        subject=subject,
        body=body,
        escalate=escalate,
    )
    return {
        "message_uid": msg.message_uid,
        "type": msg.message_type,
        "cascade_reached": msg.cascade_reached,
    }

@app.get("/nodes/{address}/inbox", tags=["Mesajlar"])
async def get_node_inbox(address: str, unread_only: bool = False):
    """Düğümün gelen kutusu"""
    messages = msg_cascade.get_inbox(address, unread_only=unread_only)
    read_set = msg_cascade.node_read.get(address, set())
    return {
        "address": address,
        "message_count": len(messages),
        "unread_count": msg_cascade.get_unread_count(address),
        "messages": [
            {
                "uid": m.message_uid,
                "type": m.message_type,
                "sender": m.sender,
                "subject": m.subject,
                "body": m.body,
                "created_at": m.created_at.isoformat(),
                "priority": m.priority,
                "is_read": m.message_uid in read_set,
            }
            for m in messages
        ],
    }


@app.post("/messages/peer", tags=["Mesajlar"])
async def send_peer_message(
    sender: str,
    recipient: str,
    subject: str,
    body: str = "",
):
    """Eşler arası doğrudan mesaj gönder"""
    msg = await msg_cascade.send_peer_message(
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
    )
    return {
        "message_uid": msg.message_uid,
        "type": "peer",
        "sender": msg.sender,
        "recipient": msg.recipient,
        "cascade_reached": msg.cascade_reached,
    }


@app.put("/nodes/{address}/inbox/{message_uid}/read", tags=["Mesajlar"])
async def mark_message_read(address: str, message_uid: str):
    """Mesajı okundu olarak işaretle"""
    success = msg_cascade.mark_as_read(address, message_uid)
    if not success:
        raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
    return {"address": address, "message_uid": message_uid, "is_read": True}


@app.put("/nodes/{address}/inbox/read-all", tags=["Mesajlar"])
async def mark_all_messages_read(address: str):
    """Düğümün tüm mesajlarını okundu işaretle"""
    count = msg_cascade.mark_all_as_read(address)
    return {"address": address, "marked_read": count}


@app.delete("/nodes/{address}/inbox/{message_uid}", tags=["Mesajlar"])
async def delete_message(address: str, message_uid: str):
    """Gelen kutusundan mesaj sil"""
    success = msg_cascade.delete_message(address, message_uid)
    if not success:
        raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
    return {"address": address, "message_uid": message_uid, "deleted": True}


@app.get("/nodes/{address}/messages/stats", tags=["Mesajlar"])
async def get_node_message_stats(address: str):
    """Düğüm bazında mesaj istatistikleri"""
    return msg_cascade.get_node_message_stats(address)


@app.get("/messages/stats", tags=["Mesajlar"])
async def get_message_statistics():
    """Sistem geneli mesajlaşma istatistikleri"""
    return msg_cascade.get_statistics()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALİTİK & İZLEME
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/analytics/overview", tags=["Analitik"])
async def analytics_overview():
    """Sistem geneli analitik"""
    return {
        "nodes": engine.get_system_overview(),
        "tasks": task_dist.get_statistics(),
        "messages": msg_cascade.get_statistics(),
    }

@app.get("/analytics/subtree/{address}", tags=["Analitik"])
async def subtree_analytics(address: str):
    """Alt ağaç analitikleri"""
    try:
        stats = await engine.aggregate_subtree_stats(address)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/health/{address}", tags=["Analitik"])
async def health_check(address: str = "L0"):
    """Sağlık kontrolü"""
    return await engine.health_check(address)

@app.post("/analytics/rebalance/{address}", tags=["Analitik"])
async def rebalance(address: str):
    """Alt ağaç yük dengeleme"""
    transfers = await engine.rebalance_subtree(address)
    return {
        "address": address,
        "transfers": transfers or [],
        "transfer_count": len(transfers) if transfers else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH İŞLEMLER (Toplu kayıt)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/batch/register-tree", tags=["Toplu İşlem"])
async def batch_register_tree(
    root_address: str = "L0",
    depth: int = 2,
):
    """
    Bir düğümün altındaki tüm düğümleri otomatik kaydet.
    
    Dikkat: depth=2 → 111 düğüm, depth=3 → 1111 düğüm
    Performans için depth ≤ 4 önerilir (11,111 düğüm)
    """
    if depth > 5:
        raise HTTPException(
            status_code=400, 
            detail=f"Max derinlik 5'tir (güvenlik). depth={depth} çok büyük."
        )
    
    registered = 0
    
    async def register_recursive(address: str, remaining_depth: int):
        nonlocal registered
        
        if address not in engine.nodes:
            addr_obj = NodeAddress.from_string(address)
            from src.utils.addressing import _level_role
            await engine.register_node(address, name=_level_role(addr_obj.level))
            registered += 1
        
        if remaining_depth > 0:
            addr_obj = NodeAddress.from_string(address)
            for child_addr in addr_obj.children:
                await register_recursive(child_addr.to_string(), remaining_depth - 1)
    
    await register_recursive(root_address, depth)
    
    return {
        "root": root_address,
        "depth": depth,
        "registered_nodes": registered,
        "total_nodes_in_system": len(engine.nodes),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EMAREULAK ENTEGRASYONU (100+ Proje Dağıtımı)
# ═══════════════════════════════════════════════════════════════════════════════

class EmareUlakProjectRequest(BaseModel):
    """EmareUlak proje talebi"""
    project_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    estimated_kb: int = 30720
    tags: List[str] = []


class EmareUlakBatchRequest(BaseModel):
    """EmareUlak toplu proje talebi"""
    projects: List[EmareUlakProjectRequest]
    parallel: bool = True
    strategy: str = "weighted"


@app.post("/emareulak/project", tags=["EmareUlak"])
async def emareulak_distribute_project(request: EmareUlakProjectRequest):
    """
    EmareUlak'tan tek proje al ve dağıt.
    
    Proje otomatik olarak uygun düğüme atanır (yük bazlı).
    """
    project = ProjectTask(
        project_id=request.project_id,
        title=request.title,
        description=request.description,
        priority=request.priority,
        estimated_kb=request.estimated_kb,
        tags=request.tags,
    )
    
    result = await emareulak.distribute_project(project)
    
    return {
        "status": result.status,
        "project_id": result.project_id,
        "task_uid": result.task_uid,
        "assigned_to": result.assigned_to,
        "subtask_count": len(result.subtasks),
        "message": result.message,
        "timestamp": result.timestamp.isoformat(),
    }


@app.post("/emareulak/batch", tags=["EmareUlak"])
async def emareulak_distribute_batch(request: EmareUlakBatchRequest):
    """
    EmareUlak'tan toplu proje al ve dağıt (100+ proje için optimize).
    
    - parallel=True: Paralel dağıtım (hızlı, 10'lu gruplar)
    - strategy: weighted, cascade, round-robin, least-loaded
    """
    # Strateji güncelle
    strategy_map = {
        "weighted": DistributionStrategy.WEIGHTED,
        "cascade": DistributionStrategy.CASCADE,
        "round-robin": DistributionStrategy.ROUND_ROBIN,
        "least-loaded": DistributionStrategy.LEAST_LOADED,
    }
    emareulak.strategy = strategy_map.get(request.strategy, DistributionStrategy.WEIGHTED)
    
    # Projeleri dönüştür
    projects = [
        ProjectTask(
            project_id=p.project_id,
            title=p.title,
            description=p.description,
            priority=p.priority,
            estimated_kb=p.estimated_kb,
            tags=p.tags,
        )
        for p in request.projects
    ]
    
    results = await emareulak.distribute_batch(projects, parallel=request.parallel)
    
    success_count = sum(1 for r in results if r.status == "success")
    error_count = len(results) - success_count
    
    return {
        "total": len(results),
        "success": success_count,
        "errors": error_count,
        "strategy": request.strategy,
        "parallel": request.parallel,
        "results": [
            {
                "project_id": r.project_id,
                "task_uid": r.task_uid,
                "assigned_to": r.assigned_to,
                "status": r.status,
                "message": r.message,
            }
            for r in results
        ],
    }


@app.get("/emareulak/status/{project_id}", tags=["EmareUlak"])
async def emareulak_get_project_status(project_id: str):
    """EmareUlak proje durumu sorgula"""
    status = await emareulak.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    
    return status


@app.get("/emareulak/status", tags=["EmareUlak"])
async def emareulak_get_all_status():
    """Tüm EmareUlak projelerinin durumu"""
    statuses = await emareulak.get_all_projects_status()
    return {
        "total_projects": len(statuses),
        "projects": statuses,
    }


@app.delete("/emareulak/project/{project_id}", tags=["EmareUlak"])
async def emareulak_cancel_project(project_id: str):
    """EmareUlak projesini iptal et"""
    success = await emareulak.cancel_project(project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Proje bulunamadı veya iptal edilemedi")
    
    return {"status": "cancelled", "project_id": project_id}


# ═══════════════════════════════════════════════════════════════════════════════
# EMARE AI WORKERS - Proje Dağıtım Sistemi
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/workers", tags=["AI Workers"])
async def get_all_workers():
    """Tüm AI worker'ları listele"""
    return {
        "total": len(workforce.workers),
        "available": len(workforce.get_available_workers()),
        "workers": [w.to_dict() for w in workforce.workers],
        "stats": workforce.get_workforce_stats()
    }


@app.get("/workers/running", tags=["AI Workers"])
async def get_running_workers():
    """
    Hangi projeler şu an yerel olarak çalışıyor?
    Her worker'ın local_port'una TCP ping gönderir.
    """
    running = await workforce.running_workers()
    return {
        "running_count": len(running),
        "workers": running,
    }


@app.post("/workers/reload", tags=["AI Workers"])
async def reload_workers():
    """
    projects.json değişti — worker listesini sıcak yeniden yükle.
    Sunucuyu yeniden başlatmadan güncel projeleri alır.
    """
    from src.emare_workers import reload_workforce as _reload
    wf = _reload()
    return {
        "status": "reloaded",
        "total_workers": len(wf.workers),
        "available": len(wf.get_available_workers()),
    }


@app.get("/workers/category/{category}", tags=["AI Workers"])
async def get_workers_by_category(category: str):
    """Kategoriye göre worker'ları filtrele (SaaS Platform, Infrastructure, vb.)"""
    workers = workforce.find_by_category(category)
    return {
        "category": category,
        "count": len(workers),
        "workers": [w.to_dict() for w in workers],
    }


@app.get("/workers/search", tags=["AI Workers"])
async def search_worker_by_name(q: str):
    """Worker'ları isimle ara (case-insensitive, kısmi eşleşme)"""
    worker = workforce.get_by_name(q)
    if not worker:
        raise HTTPException(status_code=404, detail=f"'{q}' ile eşleşen worker bulunamadı")
    return worker.to_dict()


@app.get("/workers/stats", tags=["AI Workers"])
async def get_worker_stats():
    """
    AI worker'ların detaylı istatistikleri.
    category/status/expertise dağılımı + top-5 priority.
    """
    stats = workforce.get_workforce_stats()
    return {
        "total_workers": stats["total_workers"],
        "available_workers": stats["available_workers"],
        "status_distribution": stats["by_status"],
        "category_distribution": stats["by_category"],
        "expertise_coverage": stats["by_expertise"],
        "top_workers": stats["top_priority_workers"],
    }


@app.get("/workers/{worker_id}", tags=["AI Workers"])
async def get_worker_detail(worker_id: str, memory: bool = False):
    """Worker detaylarını getir. memory=true eklenirse hafıza dosyasının öniz lemesini döndürür."""
    worker = workforce.get_worker_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker bulunamadı")
    return worker.to_dict(include_memory=memory)


class AssignTaskRequest(BaseModel):
    title: str
    description: str = ""
    requirements: List[str] = []
    max_workers: int = 3


@app.post("/workers/task/rank", tags=["AI Workers"])
async def rank_workers_for_task(req: AssignTaskRequest):
    """
    Gereksinimler için tüm uygun worker'ları match_score ile sırala.
    find_workers_with_scores kullanır — her worker'ın skomu gösterilir.
    """
    scored = workforce.find_workers_with_scores(req.requirements, max_workers=req.max_workers)
    if not scored:
        raise HTTPException(status_code=404, detail="Uygun worker bulunamadı")
    return {
        "requirements": req.requirements,
        "ranked_workers": scored,
        "top": scored[0] if scored else None,
    }


@app.post("/projects/{project_id}/cancel", tags=["AI Workers"])
async def cancel_project(project_id: str):
    """Aktif projeyi iptal et."""
    success = orchestrator.cancel_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    return {"status": "cancelled", "project_id": project_id}


@app.post("/projects/{project_id}/retry", tags=["AI Workers"])
async def retry_failed_tasks(project_id: str):
    """Başarısız task'ları yeniden dene."""
    if not orchestrator.active_projects.get(project_id):
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    retried = orchestrator.retry_failed_tasks(project_id)
    return {"project_id": project_id, "retried_tasks": retried}


@app.get("/projects/stats", tags=["AI Workers"])
async def get_project_stats():
    """Tüm projeler üzerine özet istatistik."""
    return orchestrator.get_stats()


@app.get("/workers/expertise/{expertise}", tags=["AI Workers"])
async def find_workers_by_expertise(expertise: str, limit: int = 10):
    """Belirli uzmanlık alanına sahip worker'ları bul"""
    workers = workforce.find_best_workers_for_task([expertise], max_workers=limit)
    return {
        "expertise": expertise,
        "count": len(workers),
        "workers": [w.to_dict() for w in workers]
    }

@app.post("/projects", tags=["AI Workers"])
async def create_project(project: SoftwareProject):
    """
    Yeni yazılım projesi oluştur ve AI worker'lara dağıt
    
    Proje otomatik olarak task'lara bölünür ve en uygun AI'lara atanır.
    Her AI paralel çalışır ve sonuçlar otomatik birleştirilir.
    """
    try:
        project_id = await orchestrator.start_project(project)
        return {
            "status": "started",
            "project_id": project_id,
            "message": "Proje başlatıldı ve task'lar AI worker'lara dağıtıldı",
            "track_url": f"/projects/{project_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects", tags=["AI Workers"])
async def list_projects():
    """Tüm projeleri listele"""
    return {
        "projects": orchestrator.get_all_projects()
    }

@app.get("/projects/{project_id}", tags=["AI Workers"])
async def get_project_status(project_id: str):
    """Proje durumunu ve ilerlemesini getir"""
    status = orchestrator.get_project_status(project_id)
    if not status:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    return status

@app.post("/projects/analyze", tags=["AI Workers"])
async def analyze_project(project: SoftwareProject):
    """
    Projeyi analiz et ancak başlatma (dry-run)
    
    Projenin kaç task'a bölüneceğini, hangi AI'lara atanacağını
    ve tahmini süreyi gösterir.
    """
    analysis = project_splitter.analyze_project(project)
    
    # Her task için uygun worker'ları bul
    task_assignments = []
    for task in analysis["tasks"]:
        workers = workforce.find_best_workers_for_task(task.requirements, max_workers=3)
        task_assignments.append({
            "task": {
                "id": task.id,
                "title": task.title,
                "type": task.type,
                "estimated_hours": task.estimated_hours,
                "requirements": task.requirements,
            },
            "recommended_workers": [
                {"id": w.id, "name": w.name, "priority": w.priority}
                for w in workers
            ]
        })
    
    return {
        "project_name": project.name,
        "analysis": {
            "total_tasks": analysis["total_tasks"],
            "estimated_hours": analysis["estimated_hours"],
            "parallel_potential": analysis["parallel_possible"],
        },
        "task_assignments": task_assignments,
        "workforce_availability": {
            "total_workers": len(workforce.workers),
            "available_workers": len(workforce.get_available_workers()),
        }
    }


@app.get("/emareulak/stats", tags=["EmareUlak"])
async def emareulak_statistics():
    """EmareUlak istatistikleri"""
    return emareulak.get_statistics()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS & MONITORING
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/projects/{project_id}/timeline", tags=["AI Workers"])
async def get_project_timeline(project_id: str):
    """
    Proje zaman çizelgesi - task'ların başlama/bitiş zamanları
    Gantt chart için kullanılabilir
    """
    status = orchestrator.get_project_status(project_id)
    if not status:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    
    timeline = []
    for assignment in status["assignments"]:
        timeline.append({
            "task_id": assignment["task_id"],
            "task_title": assignment["task_title"],
            "worker": assignment["worker_name"],
            "status": assignment["status"],
            "assigned_at": assignment["assigned_at"],
            "started_at": assignment.get("started_at"),
            "completed_at": assignment.get("completed_at"),
            "estimated_hours": assignment.get("estimated_hours", 0),
            "actual_duration_seconds": assignment.get("duration_seconds", 0)
        })
    
    return {
        "project_id": project_id,
        "project_name": status["project_name"],
        "timeline": sorted(timeline, key=lambda x: x["assigned_at"])
    }

@app.get("/analytics/summary", tags=["Analytics"])
async def get_analytics_summary():
    """Dashboard için genel analytics özeti"""
    stats = orchestrator.get_stats()
    worker_stats = workforce.get_workforce_stats()
    return {
        "projects": {
            "total": stats["total_projects"],
            "active": stats["active"],
            "completed": stats["completed"],
            "cancelled": stats.get("cancelled", 0),
        },
        "tasks": {
            "total": stats["total_tasks"],
            "completed": stats["completed_tasks"],
            "in_progress": stats["total_tasks"] - stats["completed_tasks"],
            "overall_progress_pct": stats["overall_progress_pct"],
        },
        "workers": {
            "total": worker_stats["total_workers"],
            "available": worker_stats["available_workers"],
            "by_status": worker_stats["by_status"],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EMARE EKOSİSTEM YÖNETİMİ  (daha önce manuel yapılan koordinasyon işleri)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/emare/health", tags=["Emare Ekosistem"])
async def emare_health(force: bool = False):
    """
    21 Emare projesinin sağlık durumunu kontrol et.

    - force=true → cache'i geç, anlık kontrol yap
    - Proje path'inin varlığı, EMARE_ORTAK_CALISMA linki ve dosya göstergesi kontrolü
    """
    results = await ecosystem.check_health(force=force)
    summary = ecosystem.get_health_summary(results)
    return {
        "summary": summary,
        "projects": [h.to_dict() for h in results],
        "checked_at": datetime.utcnow().isoformat(),
    }


@app.get("/emare/overview", tags=["Emare Ekosistem"])
async def emare_overview():
    """
    Tüm ekosisteme genel bakış — dashboard için.
    Kategori, durum dağılımı ve sağlık özeti içerir.
    """
    return await ecosystem.get_ecosystem_overview()


@app.get("/emare/projects", tags=["Emare Ekosistem"])
async def emare_list_projects():
    """Tüm 21 Emare projesini listele (anlık sağlık datası ile)"""
    health = await ecosystem.check_health()
    health_map = {h.id: h for h in health}

    projects = []
    for p in ecosystem.projects:
        entry = dict(p)
        h = health_map.get(p["id"])
        if h:
            entry["health_score"] = h.health_score
            entry["is_healthy"] = h.is_healthy
            entry["has_ortak_link"] = h.has_ortak_link
        projects.append(entry)

    return {
        "total": len(projects),
        "projects": projects,
    }


@app.get("/emare/projects/{project_id}", tags=["Emare Ekosistem"])
async def emare_get_project(project_id: str):
    """Tek proje detayı + sağlık durumu"""
    detail = await ecosystem.get_project_detail(project_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Proje bulunamadı: {project_id}")
    return detail


class DistributeRequest(BaseModel):
    method: str = "symlink"   # "symlink" veya "copy"
    force: bool = False


@app.post("/emare/distribute", tags=["Emare Ekosistem"])
async def emare_distribute(req: DistributeRequest = DistributeRequest()):
    """
    EMARE_ORTAK_CALISMA dosyalarını tüm projelere dağıt.

    - method=symlink (varsayılan): Her proje klasörüne symlink kur
    - method=copy: Dosyaları fiziksel kopyala
    - force=true: Mevcut linklerin üzerine yaz

    Bu endpoint daha önce elle çalıştırılan distribute_ortak_calisma.py'nin yerini alır.
    """
    result = await ecosystem.distribute_ortak_calisma(
        method=req.method, force=req.force
    )
    return result.to_dict()


@app.post("/emare/symlinks/repair", tags=["Emare Ekosistem"])
async def emare_repair_symlinks():
    """
    Kırık EMARE_ORTAK_CALISMA symlink'lerini tespit et ve onar.
    Bu endpoint convert_to_symlink.py'nin işini otomatize eder.
    """
    return await ecosystem.repair_symlinks()


@app.post("/emare/dosya-yapisi/refresh", tags=["Emare Ekosistem"])
async def emare_refresh_dosya_yapisi():
    """
    Tüm projeler için DOSYA_YAPISI.md'yi yenile.
    Her projenin kök klasöründeki dosya yapısını Markdown formatında yazar.
    Bu endpoint create_dosya_yapisi.py'nin işini otomatize eder.
    """
    return await ecosystem.refresh_dosya_yapisi()


@app.post("/emare/task/assign", tags=["Emare Ekosistem"])
async def emare_assign_task(req: AssignTaskRequest):
    """
    Görevi en uygun AI worker'a ata.

    requirements listesi örn: ["python", "backend", "ai"]
    Uygun worker'ları uzmanlığa + önceliğe göre sıralar ve önerir.
    """
    best_workers = workforce.find_best_workers_for_task(
        req.requirements, max_workers=req.max_workers
    )
    if not best_workers:
        raise HTTPException(
            status_code=404,
            detail=f"Gereksinimler için uygun worker bulunamadı: {req.requirements}",
        )

    return {
        "task_title": req.title,
        "requirements": req.requirements,
        "recommended_workers": [
            {
                "id": w.id,
                "name": w.name,
                "priority": w.priority,
                "expertise": w.expertise,
                "status": w.status,
                "path": w.path if hasattr(w, 'path') else None,
            }
            for w in best_workers
        ],
        "primary_assignee": {
            "id": best_workers[0].id,
            "name": best_workers[0].name,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DERGAH SOHBET ODASI
# ═══════════════════════════════════════════════════════════════════════════════

class DergahSendRequest(BaseModel):
    room: str = "genel"
    sender_id: str
    sender_name: str
    content: str
    sender_icon: str = "🧙‍♂️"
    message_type: str = "chat"
    metadata: dict = {}
    reply_to: Optional[str] = None


class DergahReactionRequest(BaseModel):
    emoji: str
    sender_id: str


class DergahGithubEventRequest(BaseModel):
    event_type: str  # push, issue, pr, webhook, deploy
    repo_name: str
    description: str
    url: str = ""
    actor: str = ""


class DergahFileShareRequest(BaseModel):
    room: str = "genel"
    sender_id: str
    sender_name: str
    file_path: str
    file_size: int = 0
    description: str = ""
    sender_icon: str = "🧙‍♂️"


class DergahDeployRequest(BaseModel):
    project_id: str
    project_name: str
    version: str = ""
    status: str = "success"


@app.get("/dergah/rooms", tags=["Dergah Sohbet"])
async def dergah_rooms():
    """Tüm dergah odalarını ve mesaj sayılarını getir."""
    return dergah.get_rooms()


@app.get("/dergah/messages", tags=["Dergah Sohbet"])
async def dergah_messages(
    room: str = "genel",
    limit: int = 50,
    before: Optional[str] = None,
    after: Optional[str] = None,
    message_type: Optional[str] = None,
):
    """Oda mesajlarını getir (pagination desteği)."""
    return dergah.get_messages(room, limit, before, after, message_type)


@app.post("/dergah/messages", tags=["Dergah Sohbet"])
async def dergah_send(req: DergahSendRequest):
    """Dergah odasına mesaj gönder."""
    msg = dergah.send_message(
        room=req.room,
        sender_id=req.sender_id,
        sender_name=req.sender_name,
        content=req.content,
        sender_icon=req.sender_icon,
        message_type=req.message_type,
        metadata=req.metadata,
        reply_to=req.reply_to,
    )
    return msg.to_dict()


@app.get("/dergah/messages/{uid}", tags=["Dergah Sohbet"])
async def dergah_get_message(uid: str):
    """Tek mesaj getir."""
    msg = dergah.get_message(uid)
    if not msg:
        raise HTTPException(404, "Mesaj bulunamadı")
    return msg


@app.delete("/dergah/messages/{uid}", tags=["Dergah Sohbet"])
async def dergah_delete_message(uid: str):
    """Mesajı sil."""
    ok = dergah.delete_message(uid)
    if not ok:
        raise HTTPException(404, "Mesaj bulunamadı")
    return {"deleted": True, "uid": uid}


@app.post("/dergah/messages/{uid}/reaction", tags=["Dergah Sohbet"])
async def dergah_add_reaction(uid: str, req: DergahReactionRequest):
    """Mesaja reaksiyon ekle."""
    ok = dergah.add_reaction(uid, req.emoji, req.sender_id)
    if not ok:
        raise HTTPException(404, "Mesaj bulunamadı")
    return {"ok": True}


@app.delete("/dergah/messages/{uid}/reaction", tags=["Dergah Sohbet"])
async def dergah_remove_reaction(uid: str, req: DergahReactionRequest):
    """Reaksiyonu kaldır."""
    ok = dergah.remove_reaction(uid, req.emoji, req.sender_id)
    return {"ok": ok}


@app.post("/dergah/messages/{uid}/pin", tags=["Dergah Sohbet"])
async def dergah_pin(uid: str):
    """Mesajı sabitle."""
    ok = dergah.pin_message(uid)
    if not ok:
        raise HTTPException(404, "Mesaj bulunamadı")
    return {"pinned": True}


@app.delete("/dergah/messages/{uid}/pin", tags=["Dergah Sohbet"])
async def dergah_unpin(uid: str):
    """Sabitlenmiş mesajı kaldır."""
    dergah.unpin_message(uid)
    return {"unpinned": True}


@app.get("/dergah/pinned", tags=["Dergah Sohbet"])
async def dergah_pinned(room: str = "genel"):
    """Sabitlenen mesajları getir."""
    return dergah.get_pinned(room)


@app.post("/dergah/github-event", tags=["Dergah Sohbet"])
async def dergah_github_event(req: DergahGithubEventRequest):
    """GitHub olayını dergaha bildir."""
    msg = dergah.notify_github_event(
        event_type=req.event_type,
        repo_name=req.repo_name,
        description=req.description,
        url=req.url,
        actor=req.actor,
    )
    return msg.to_dict()


@app.post("/dergah/file-share", tags=["Dergah Sohbet"])
async def dergah_file_share(req: DergahFileShareRequest):
    """Dosya paylaşımı gönder."""
    msg = dergah.share_file(
        room=req.room,
        sender_id=req.sender_id,
        sender_name=req.sender_name,
        file_path=req.file_path,
        file_size=req.file_size,
        description=req.description,
        sender_icon=req.sender_icon,
    )
    return msg.to_dict()


@app.post("/dergah/deploy-notify", tags=["Dergah Sohbet"])
async def dergah_deploy_notify(req: DergahDeployRequest):
    """Deploy bildirimini dergaha gönder."""
    msg = dergah.notify_deploy(
        project_id=req.project_id,
        project_name=req.project_name,
        version=req.version,
        status=req.status,
    )
    return msg.to_dict()


@app.post("/dergah/heartbeat/{dervis_id}", tags=["Dergah Sohbet"])
async def dergah_heartbeat(dervis_id: str):
    """Dervişin online olduğunu bildir."""
    dergah.heartbeat(dervis_id)
    return {"ok": True, "dervis_id": dervis_id}


@app.get("/dergah/online", tags=["Dergah Sohbet"])
async def dergah_online(timeout: int = 5):
    """Online dervişleri getir."""
    return dergah.get_online_dervishes(timeout)


@app.get("/dergah/search", tags=["Dergah Sohbet"])
async def dergah_search(q: str, room: Optional[str] = None, limit: int = 20):
    """Dergah mesajlarında arama."""
    return dergah.search_messages(q, room, limit)


@app.get("/dergah/stats", tags=["Dergah Sohbet"])
async def dergah_stats():
    """Dergah istatistikleri."""
    return dergah.get_stats()


# ═══════════════════════════════════════════════════════════════════════════════
# DERVİŞ YETENEKLERİ (CAPABILITIES)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/dervish/capabilities", tags=["Derviş Yetenekleri"])
async def dervish_all_capabilities():
    """Tüm dervişlerin yeteneklerini getir."""
    return get_all_capabilities()


@app.get("/dervish/capabilities/summary", tags=["Derviş Yetenekleri"])
async def dervish_capabilities_summary():
    """Derviş yetenekleri özet istatistikleri."""
    return get_capabilities_summary()


@app.get("/dervish/{dervish_id}/capabilities", tags=["Derviş Yetenekleri"])
async def dervish_capabilities(dervish_id: str):
    """Tek dervişin tüm yeteneklerini getir (iç/dış API'ler, servisler, entegrasyonlar)."""
    caps = get_capabilities(dervish_id)
    if not caps:
        raise HTTPException(404, f"Derviş bulunamadı: {dervish_id}")
    return {"dervish_id": dervish_id, **caps}

