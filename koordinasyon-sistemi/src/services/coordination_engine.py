"""
Koordinasyon Motoru
===================

Hiyerarşik yapıdaki tüm koordinasyon işlemlerini yönetir:
1. Düğüm yaşam döngüsü yönetimi
2. Durum toplama (aggregation) - alttan üste
3. Yük dengeleme
4. Sağlık kontrolü
5. Otomatik ölçekleme kararları
"""

from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

from src import HIERARCHY_DEPTH, BRANCH_FACTOR
from src.utils.addressing import NodeAddress, format_node_count

logger = structlog.get_logger()


# ─── Bellek İçi Düğüm Temsili (Hızlı İşlem) ────────────────────────────────

@dataclass
class LiveNode:
    """Çalışma zamanında bir düğümün durumunu temsil eder."""
    address: NodeAddress
    status: str = "active"
    capacity: int = 100
    current_load: int = 0
    efficiency: float = 1.0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    
    # Alt ağaç toplu metrikleri (cache)
    _subtree_stats: Optional[dict] = field(default=None, repr=False)
    _stats_valid_until: Optional[datetime] = field(default=None, repr=False)
    
    @property
    def load_pct(self) -> float:
        if self.capacity == 0:
            return 100.0
        return (self.current_load / self.capacity) * 100
    
    @property
    def is_available(self) -> bool:
        return self.status == "active" and self.load_pct < 90
    
    @property
    def is_healthy(self) -> bool:
        """Düğüm sağlıklı mı? (Son 5 dk içinde heartbeat)"""
        if self.status == "offline":
            return False
        return (datetime.utcnow() - self.last_heartbeat) < timedelta(minutes=5)


class CoordinationEngine:
    """
    Ana koordinasyon motoru.
    
    Her seviyedeki düğümleri yönetir ve hiyerarşi boyunca
    görev dağıtımı, durum toplama ve iletişim sağlar.
    
    Ölçekleme stratejisi:
    - Seviye 0-3: Merkezi veritabanında doğrudan yönetim
    - Seviye 4-6: Bölgesel koordinatörler tarafından kademeli yönetim
    - Seviye 7-10: Yerel takım kaptanları tarafından otonom yönetim
    """
    
    def __init__(self):
        self.nodes: dict[str, LiveNode] = {}
        self._running = False
        self._aggregation_interval = 30  # saniye
        
        # Entegre servisler (setter injection - döngüsel import önlemi)
        self._message_cascade = None  # MessageCascade referansı
        self._task_distributor = None  # TaskDistributor referansı
    
    def set_message_cascade(self, cascade) -> None:
        """MessageCascade servisini engine'e bağla"""
        self._message_cascade = cascade
        logger.info("mesaj_sistemi_bağlandı")
    
    def set_task_distributor(self, distributor) -> None:
        """TaskDistributor servisini engine'e bağla"""
        self._task_distributor = distributor
        logger.info("görev_dağıtıcı_bağlandı")
    
    # ─── Düğüm Yönetimi ─────────────────────────────────────────────────

    async def register_node(self, address: str, name: str = None, **kwargs) -> LiveNode:
        """Yeni bir düğümü sisteme kaydet"""
        node_addr = NodeAddress.from_string(address)
        
        # Ebeveyn kontrolü (kök hariç)
        if node_addr.level > 0:
            parent = node_addr.parent
            if parent.to_string() not in self.nodes:
                # Ebeveyn yoksa önce onu oluştur (lazy initialization)
                await self.register_node(parent.to_string())
        
        node = LiveNode(
            address=node_addr,
            **{k: v for k, v in kwargs.items() if k in LiveNode.__dataclass_fields__}
        )
        
        self.nodes[address] = node
        logger.info("düğüm_kaydedildi", address=address, level=node_addr.level)
        return node
    
    async def heartbeat(self, address: str) -> dict:
        """Düğümden yaşam sinyali al"""
        if address not in self.nodes:
            raise ValueError(f"Bilinmeyen düğüm: {address}")
        
        node = self.nodes[address]
        node.last_heartbeat = datetime.utcnow()
        
        # Düğümün alt ağaç durumunu döndür
        return {
            "address": address,
            "status": "ok",
            "pending_tasks": await self._get_pending_tasks(address),
            "pending_messages": await self._get_pending_messages(address),
        }
    
    async def update_node_status(self, address: str, status: str, load: int = None):
        """Düğüm durumunu güncelle"""
        if address not in self.nodes:
            raise ValueError(f"Bilinmeyen düğüm: {address}")
        
        node = self.nodes[address]
        old_status = node.status
        node.status = status
        if load is not None:
            node.current_load = load
        
        logger.info("düğüm_güncellendi", address=address, 
                    old_status=old_status, new_status=status)
        
        # Ebeveynin toplu metriklerini güncelle
        await self._propagate_status_change(address)
        
        # Kritik durum değişimlerinde otomatik mesaj gönder
        await self._notify_status_change(address, old_status, status)
        
        # Yük kontrolü — aşırı yükte de bildirim
        if load is not None and node.load_pct > 90:
            await self._notify_overload(address)
    
    # ─── Durum Toplama (Aggregation) ─────────────────────────────────────
    
    async def aggregate_subtree_stats(self, address: str) -> dict:
        """
        Bir düğümün alt ağaç istatistiklerini topla.
        
        Bu işlem kademeli olarak çalışır:
        - Her çocuk kendi alt ağacını toplar
        - Ebeveyn, çocukların sonuçlarını birleştirir
        
        9 milyar düğüm için bu işlem dağıtık olarak yapılır:
        her düğüm sadece kendi 10 çocuğunun özetini alır.
        """
        node_addr = NodeAddress.from_string(address)
        
        # Yaprak düğüm
        if node_addr.level >= HIERARCHY_DEPTH:
            node = self.nodes.get(address)
            if not node:
                return self._empty_stats(address)
            return {
                "root_address": address,
                "total_nodes": 1,
                "active_nodes": 1 if node.status == "active" else 0,
                "idle_nodes": 1 if node.status == "idle" else 0,
                "offline_nodes": 1 if node.status == "offline" else 0,
                "avg_efficiency": node.efficiency,
                "avg_load_pct": node.load_pct,
                "health_score": 100.0 if node.is_healthy else 0.0,
            }
        
        # Çocuk düğümlerin istatistiklerini topla
        children_stats = []
        for child_addr in node_addr.children:
            child_str = child_addr.to_string()
            if child_str in self.nodes:
                stats = await self.aggregate_subtree_stats(child_str)
                children_stats.append(stats)
        
        if not children_stats:
            return self._empty_stats(address)
        
        # Birleştir
        total_nodes = 1 + sum(s["total_nodes"] for s in children_stats)
        active = sum(s["active_nodes"] for s in children_stats)
        idle = sum(s["idle_nodes"] for s in children_stats)
        offline = sum(s["offline_nodes"] for s in children_stats)
        
        node = self.nodes.get(address)
        if node and node.status == "active":
            active += 1
        elif node and node.status == "idle":
            idle += 1
        elif node and node.status == "offline":
            offline += 1
        
        avg_eff = sum(s["avg_efficiency"] * s["total_nodes"] for s in children_stats)
        avg_eff = avg_eff / max(total_nodes - 1, 1)
        
        avg_load = sum(s["avg_load_pct"] * s["total_nodes"] for s in children_stats)
        avg_load = avg_load / max(total_nodes - 1, 1)
        
        health = (active / max(total_nodes, 1)) * 100
        
        result = {
            "root_address": address,
            "total_nodes": total_nodes,
            "active_nodes": active,
            "idle_nodes": idle,
            "offline_nodes": offline,
            "avg_efficiency": round(avg_eff, 3),
            "avg_load_pct": round(avg_load, 1),
            "health_score": round(health, 1),
        }
        
        # Cache'e kaydet
        if node:
            node._subtree_stats = result
            node._stats_valid_until = datetime.utcnow() + timedelta(seconds=30)
        
        return result
    
    # ─── Yük Dengeleme ───────────────────────────────────────────────────
    
    async def find_least_loaded_child(self, parent_address: str) -> Optional[str]:
        """Ebeveynin en az yüklü çocuğunu bul"""
        parent = NodeAddress.from_string(parent_address)
        
        best = None
        best_load = float("inf")
        
        for child_addr in parent.children:
            child_str = child_addr.to_string()
            if child_str in self.nodes:
                node = self.nodes[child_str]
                if node.is_available and node.load_pct < best_load:
                    best = child_str
                    best_load = node.load_pct
        
        return best
    
    async def find_optimal_path(self, from_level: int = 0, 
                                 task_weight: int = 10) -> list[str]:
        """
        Kökten yaprak düğüme kadar en uygun yolu bul.
        
        Her seviyede en az yüklü ve en verimli çocuğu seçer.
        Bu, görev ataması için kullanılır.
        """
        path = []
        current_address = "L0"
        
        for level in range(from_level, HIERARCHY_DEPTH):
            current = NodeAddress.from_string(current_address)
            
            # Çocukları değerlendir
            candidates = []
            for child_addr in current.children:
                child_str = child_addr.to_string()
                if child_str in self.nodes:
                    node = self.nodes[child_str]
                    if node.is_available:
                        # Skor: düşük yük + yüksek verimlilik = iyi
                        score = (100 - node.load_pct) * node.efficiency
                        candidates.append((child_str, score))
            
            if not candidates:
                break
            
            # En iyi adayı seç
            candidates.sort(key=lambda x: x[1], reverse=True)
            best = candidates[0][0]
            path.append(best)
            current_address = best
        
        return path
    
    async def rebalance_subtree(self, address: str):
        """
        Bir alt ağaçtaki yükü yeniden dengele.
        
        Aşırı yüklü çocuklardan boşta olanlara görev taşır.
        """
        node_addr = NodeAddress.from_string(address)
        children_data = []
        
        for child_addr in node_addr.children:
            child_str = child_addr.to_string()
            if child_str in self.nodes:
                node = self.nodes[child_str]
                children_data.append({
                    "address": child_str,
                    "load": node.current_load,
                    "capacity": node.capacity,
                    "load_pct": node.load_pct,
                })
        
        if len(children_data) < 2:
            return
        
        avg_load = sum(c["load"] for c in children_data) / len(children_data)
        
        overloaded = [c for c in children_data if c["load"] > avg_load * 1.3]
        underloaded = [c for c in children_data if c["load"] < avg_load * 0.7]
        
        transfers = []
        for over in overloaded:
            excess = int(over["load"] - avg_load)
            for under in underloaded:
                available = int(avg_load - under["load"])
                transfer = min(excess, available)
                if transfer > 0:
                    transfers.append({
                        "from": over["address"],
                        "to": under["address"],
                        "amount": transfer,
                    })
                    excess -= transfer
                    if excess <= 0:
                        break
        
        # Transferleri uygula
        for t in transfers:
            from_node = self.nodes[t["from"]]
            to_node = self.nodes[t["to"]]
            from_node.current_load -= t["amount"]
            to_node.current_load += t["amount"]
            logger.info("yük_transferi", **t)
        
        return transfers
    
    # ─── Sağlık Kontrolü ────────────────────────────────────────────────
    
    async def health_check(self, address: str = "L0") -> dict:
        """
        Hiyerarşik sağlık kontrolü.
        
        Kademeli olarak yukarıdan aşağı kontrol yapar.
        Sorunlu düğümleri tespit eder ve raporlar.
        """
        node_addr = NodeAddress.from_string(address)
        node = self.nodes.get(address)
        
        issues = []
        
        if not node:
            return {"address": address, "healthy": False, 
                    "issues": ["Düğüm kayıtlı değil"]}
        
        # Heartbeat kontrolü
        if not node.is_healthy:
            issues.append(f"Son heartbeat: {node.last_heartbeat}")
        
        # Aşırı yük kontrolü
        if node.load_pct > 90:
            issues.append(f"Aşırı yük: %{node.load_pct:.0f}")
        
        # Düşük verimlilik
        if node.efficiency < 0.5:
            issues.append(f"Düşük verimlilik: {node.efficiency:.2f}")
        
        # Çocuk düğümleri kontrol et
        children_health = []
        if node_addr.level < HIERARCHY_DEPTH:
            for child_addr in node_addr.children:
                child_str = child_addr.to_string()
                if child_str in self.nodes:
                    child_health = await self.health_check(child_str)
                    children_health.append(child_health)
                    if not child_health["healthy"]:
                        issues.append(
                            f"Sağlıksız çocuk: {child_str} "
                            f"({len(child_health['issues'])} sorun)"
                        )
        
        return {
            "address": address,
            "healthy": len(issues) == 0,
            "issues": issues,
            "status": node.status,
            "load_pct": node.load_pct,
            "efficiency": node.efficiency,
            "children_health": children_health,
        }
    
    # ─── Yardımcı Metotlar ──────────────────────────────────────────────
    
    def _empty_stats(self, address: str) -> dict:
        return {
            "root_address": address,
            "total_nodes": 0,
            "active_nodes": 0,
            "idle_nodes": 0,
            "offline_nodes": 0,
            "avg_efficiency": 0.0,
            "avg_load_pct": 0.0,
            "health_score": 0.0,
        }
    
    async def _propagate_status_change(self, address: str):
        """Durum değişikliğini ata düğümlere yay"""
        node_addr = NodeAddress.from_string(address)
        current = node_addr.parent
        
        while current:
            parent_str = current.to_string()
            if parent_str in self.nodes:
                parent_node = self.nodes[parent_str]
                parent_node._subtree_stats = None  # Cache'i invalidate et
            current = current.parent if current.level > 0 else None
    
    async def _get_pending_tasks(self, address: str) -> int:
        """Düğümün bekleyen görev sayısı"""
        if self._task_distributor is None:
            return 0
        tasks = self._task_distributor.get_node_tasks(address)
        return sum(1 for t in tasks if t.status in ("pending", "assigned"))
    
    async def _get_pending_messages(self, address: str) -> int:
        """Düğümün okunmamış mesaj sayısı"""
        if self._message_cascade is None:
            return 0
        return self._message_cascade.get_unread_count(address)
    
    # ─── Otomatik Mesajlaşma ─────────────────────────────────────────────
    
    async def _notify_status_change(
        self, address: str, old_status: str, new_status: str
    ):
        """
        Kritik durum değişimlerinde mesaj cascade üzerinden bildirim gönder.
        
        - offline → ebeveyne eskalasyon
        - aşırı yük (>90%) → ebeveyne rapor
        - active'e dönüş → ebeveyne rapor
        """
        if self._message_cascade is None:
            return
        
        if old_status == new_status:
            return
        
        node = self.nodes.get(address)
        if not node:
            return
        
        # Düğüm çevrimdışı oldu → eskalasyon
        if new_status == "offline":
            await self._message_cascade.send_report(
                sender=address,
                subject=f"[OTOMATİK] Düğüm çevrimdışı: {address}",
                body=f"Düğüm {address} durumu {old_status} → offline olarak değişti.",
                data={"event": "node_offline", "address": address},
                escalate=True,
            )
            logger.warning("otomatik_eskalasyon", address=address, reason="offline")
        
        # Düğüm tekrar aktif oldu → bilgi raporu
        elif new_status == "active" and old_status in ("offline", "maintenance"):
            await self._message_cascade.send_report(
                sender=address,
                subject=f"[OTOMATİK] Düğüm tekrar aktif: {address}",
                body=f"Düğüm {address} durumu {old_status} → active olarak değişti.",
                data={"event": "node_recovered", "address": address},
            )
            logger.info("otomatik_bildirim", address=address, reason="recovered")
    
    async def _notify_overload(self, address: str):
        """Aşırı yük tespitinde ebeveyne eskalasyon gönder"""
        if self._message_cascade is None:
            return
        
        node = self.nodes.get(address)
        if not node or node.load_pct <= 90:
            return
        
        await self._message_cascade.send_report(
            sender=address,
            subject=f"[OTOMATİK] Aşırı yük: {address} (%{node.load_pct:.0f})",
            body=f"Düğüm {address} yükü %{node.load_pct:.0f} ile kritik seviyede.",
            data={
                "event": "node_overloaded",
                "address": address,
                "load_pct": node.load_pct,
            },
            escalate=True,
        )
        logger.warning("otomatik_eskalasyon", address=address, reason="overload")
    
    # ─── İstatistikler ───────────────────────────────────────────────────
    
    def get_system_overview(self) -> dict:
        """Sistem geneli özet"""
        total = len(self.nodes)
        active = sum(1 for n in self.nodes.values() if n.status == "active")
        idle = sum(1 for n in self.nodes.values() if n.status == "idle")
        offline = sum(1 for n in self.nodes.values() if n.status == "offline")
        
        level_dist = {}
        for addr, node in self.nodes.items():
            lvl = node.address.level
            if lvl not in level_dist:
                level_dist[lvl] = {"total": 0, "active": 0}
            level_dist[lvl]["total"] += 1
            if node.status == "active":
                level_dist[lvl]["active"] += 1
        
        avg_load = 0
        if total > 0:
            avg_load = sum(n.load_pct for n in self.nodes.values()) / total
        
        return {
            "total_registered_nodes": total,
            "active_nodes": active,
            "idle_nodes": idle,
            "offline_nodes": offline,
            "avg_load_pct": round(avg_load, 1),
            "level_distribution": level_dist,
            "hierarchy_depth": HIERARCHY_DEPTH,
            "branch_factor": BRANCH_FACTOR,
            "theoretical_max_nodes": format_node_count(sum(10**i for i in range(11))),
        }
