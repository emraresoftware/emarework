"""
Celery Background Tasks - Periyodik ve async işler
"""
import asyncio
from datetime import datetime, timezone, timedelta
from src.celery_app import app  # type: ignore
from src.config import settings
from src.db.database import AsyncSessionLocal
from src.db.repository import NodeRepository, TaskRepository, MessageRepository, MetricsRepository
from src.cache import invalidate_node_cache, cache_node_stats
import structlog

logger = structlog.get_logger()


def run_async(coro):
    """Async fonksiyonu sync Celery task'ta çalıştır"""
    return asyncio.run(coro)


@app.task(name="src.tasks.check_node_health")
def check_node_health():
    """
    Düğüm sağlık kontrolü - heartbeat timeout kontrolü
    Her 5 dakikada bir çalışır
    """
    async def _check():
        async with AsyncSessionLocal() as db:
            node_repo = NodeRepository(db)
            
            # Tüm düğümleri kontrol et
            from sqlalchemy import select
            from src.db.models import Node
            
            result = await db.execute(select(Node))
            nodes = list(result.scalars().all())
            
            timeout = timedelta(seconds=300)  # 5 dakika
            now = datetime.now(timezone.utc)
            offline_count = 0
            
            for node in nodes:
                if node.status == "active":
                    time_since_heartbeat = now - node.last_heartbeat
                    if time_since_heartbeat > timeout:
                        # Offline yap
                        from sqlalchemy import update
                        await db.execute(
                            update(Node)
                            .where(Node.address == node.address)
                            .values(status="offline")
                        )
                        offline_count += 1
                        logger.warning("node_marked_offline", 
                                     address=node.address,
                                     last_heartbeat=node.last_heartbeat)
            
            await db.commit()
            
            logger.info("health_check_completed", 
                       total_nodes=len(nodes),
                       offline_count=offline_count)
            
            return {"total_nodes": len(nodes), "offline_count": offline_count}
    
    return run_async(_check())


@app.task(name="src.tasks.aggregate_subtree_stats")
def aggregate_subtree_stats():
    """
    Alt ağaç istatistiklerini topla - alttan üste
    Her 30 saniyede bir çalışır
    """
    async def _aggregate():
        async with AsyncSessionLocal() as db:
            node_repo = NodeRepository(db)
            metrics_repo = MetricsRepository(db)
            
            from src import HIERARCHY_DEPTH
            
            aggregated_count = 0
            
            # Alttan üste doğru (L10 → L0)
            for level in range(HIERARCHY_DEPTH, -1, -1):
                nodes = await node_repo.get_by_level(level)
                
                for node in nodes:
                    # Alt düğümlerin metriklerini topla
                    children = await node_repo.get_children(node.address)
                    
                    total_descendants = len(children)
                    active_descendants = sum(1 for c in children if c.status == "active")
                    total_load = sum(c.current_load for c in children)
                    total_capacity = sum(c.capacity for c in children)
                    avg_efficiency = (
                        sum(c.efficiency for c in children) / len(children)
                        if children else node.efficiency
                    )
                    
                    # Görev istatistikleri
                    from sqlalchemy import select, func
                    from src.db.models import Task
                    
                    task_stats = await db.execute(
                        select(
                            func.count(Task.id).filter(Task.status == "pending").label("pending"),
                            func.count(Task.id).filter(Task.status == "in_progress").label("in_progress"),
                            func.count(Task.id).filter(Task.status == "completed").label("completed"),
                            func.count(Task.id).filter(Task.status == "failed").label("failed"),
                        ).where(Task.assigned_to == node.address)
                    )
                    stats = task_stats.one()
                    
                    # Metrikleri kaydet
                    await metrics_repo.upsert(
                        node.address,
                        total_descendants=total_descendants,
                        active_descendants=active_descendants,
                        total_load=total_load,
                        total_capacity=total_capacity,
                        avg_efficiency=avg_efficiency,
                        pending_tasks=stats.pending or 0,
                        in_progress_tasks=stats.in_progress or 0,
                        completed_tasks=stats.completed or 0,
                        failed_tasks=stats.failed or 0,
                        is_stale=False,
                    )
                    
                    # Cache'e de yaz
                    await cache_node_stats(node.address, {
                        "descendants": total_descendants,
                        "active": active_descendants,
                        "load": total_load,
                        "capacity": total_capacity,
                        "efficiency": avg_efficiency,
                    })
                    
                    aggregated_count += 1
            
            await db.commit()
            
            logger.info("stats_aggregated", count=aggregated_count)
            return {"aggregated_count": aggregated_count}
    
    return run_async(_aggregate())


@app.task(name="src.tasks.cleanup_expired_messages")
def cleanup_expired_messages():
    """
    Süresi dolmuş mesajları temizle
    Her 10 dakikada bir çalışır
    """
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import delete
            from src.db.models import Message
            
            now = datetime.now(timezone.utc)
            
            result = await db.execute(
                delete(Message)
                .where(Message.expires_at < now)
                .where(Message.status != "read")
            )
            
            await db.commit()
            
            deleted_count = getattr(result, 'rowcount', 0)
            logger.info("messages_cleaned_up", count=deleted_count)
            
            return {"deleted_count": deleted_count}
    
    return run_async(_cleanup())


@app.task(name="src.tasks.rebalance_node_loads")
def rebalance_node_loads():
    """
    Düğüm yüklerini dengele - aşırı yüklü düğümleri hafiflet
    Her 10 dakikada bir çalışır
    """
    async def _rebalance():
        async with AsyncSessionLocal() as db:
            node_repo = NodeRepository(db)
            task_repo = TaskRepository(db)
            
            from src import HIERARCHY_DEPTH
            rebalanced_count = 0
            
            for level in range(HIERARCHY_DEPTH + 1):
                nodes = await node_repo.get_by_level(level)
                
                # Aşırı yüklü düğümleri bul
                overloaded = [
                    n for n in nodes 
                    if n.load_pct > settings.overload_threshold_pct
                ]
                
                # Az yüklü düğümleri bul
                underloaded = [
                    n for n in nodes 
                    if n.load_pct < 50 and n.status == "active"
                ]
                
                if not (overloaded and underloaded):
                    continue
                
                # Her aşırı yüklü düğümden görev taşı
                for overload_node in overloaded:
                    pending_tasks = await task_repo.get_by_node(
                        overload_node.address, 
                        status="pending"
                    )
                    
                    if not pending_tasks:
                        continue
                    
                    # En az yüklü düğümü seç
                    target = min(underloaded, key=lambda n: n.load_pct)
                    
                    # İlk pending task'ı taşı
                    task = pending_tasks[0]
                    
                    from sqlalchemy import update
                    from src.db.models import Task
                    
                    await db.execute(
                        update(Task)
                        .where(Task.id == task.id)
                        .values(assigned_to=target.address)
                    )
                    
                    # Yükleri güncelle
                    await node_repo.update_load(
                        overload_node.address, 
                        overload_node.current_load - task.weight
                    )
                    await node_repo.update_load(
                        target.address, 
                        target.current_load + task.weight
                    )
                    
                    # Cache'leri invalidate et
                    await invalidate_node_cache(overload_node.address)
                    await invalidate_node_cache(target.address)
                    
                    rebalanced_count += 1
                    
                    logger.info("task_rebalanced",
                              task_uid=task.task_uid,
                              from_node=overload_node.address,
                              to_node=target.address)
            
            await db.commit()
            
            logger.info("rebalance_completed", count=rebalanced_count)
            return {"rebalanced_count": rebalanced_count}
    
    return run_async(_rebalance())


@app.task(name="src.tasks.test_celery")
def test_celery():
    """Celery test görevi"""
    logger.info("celery_test_task_executed")
    return {"ok": True, "timestamp": datetime.utcnow().isoformat()}


# ═══════════════════════════════════════════════════════════════════════════════
# EMARE EKOSİSTEM GÖREVLERİ
# ═══════════════════════════════════════════════════════════════════════════════

@app.task(name="src.tasks.emare_health_check")
def emare_health_check():
    """
    21 Emare projesinin sağlık durumunu kontrol et.
    Her 5 dakikada bir çalışır.
    Sonuçları loglar ve kritik sorunları işaretler.
    """
    async def _check():
        from src.emare_ecosystem import get_ecosystem
        eco = get_ecosystem()
        results = await eco.check_health(force=True)
        summary = eco.get_health_summary(results)

        unhealthy = [h.id for h in results if not h.is_healthy]
        no_link = [h.id for h in results if h.exists and not h.has_ortak_link]

        logger.info(
            "emare_ecosystem_health",
            total=summary["total_projects"],
            healthy=summary["healthy"],
            unhealthy=summary["unhealthy"],
            ecosystem_status=summary["ecosystem_status"],
        )

        if unhealthy:
            logger.warning("unhealthy_projects", projects=unhealthy)
        if no_link:
            logger.warning("missing_ortak_link", projects=no_link)

        return {
            "summary": summary,
            "unhealthy": unhealthy,
            "missing_ortak_link": no_link,
            "checked_at": datetime.utcnow().isoformat(),
        }

    return run_async(_check())


@app.task(name="src.tasks.emare_repair_symlinks")
def emare_repair_symlinks():
    """
    Kırık EMARE_ORTAK_CALISMA symlink'lerini onar.
    Her 30 dakikada bir çalışır.
    """
    async def _repair():
        from src.emare_ecosystem import get_ecosystem
        eco = get_ecosystem()
        result = await eco.repair_symlinks()
        if result["broken_found"] > 0:
            logger.warning(
                "symlinks_repaired",
                broken=result["broken_found"],
                repaired=result["repaired"],
            )
        return result

    return run_async(_repair())


@app.task(name="src.tasks.emare_refresh_dosya_yapisi")
def emare_refresh_dosya_yapisi():
    """
    Tüm projelerin DOSYA_YAPISI.md dosyasını yenile.
    Her gün gece 03:00'de çalışır (beat_schedule'da tanımlı).
    """
    async def _refresh():
        from src.emare_ecosystem import get_ecosystem
        eco = get_ecosystem()
        result = await eco.refresh_dosya_yapisi()
        logger.info(
            "dosya_yapisi_refreshed",
            updated=result["updated"],
            skipped=result["skipped"],
            failed=result["failed"],
        )
        return result

    return run_async(_refresh())
