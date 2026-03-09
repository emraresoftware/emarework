"""
Test Suite - Hive Coordinator
"""
import pytest
import pytest_asyncio
import asyncio
from src.utils.addressing import NodeAddress, level_summary, format_node_count
from src.services.coordination_engine import CoordinationEngine
from src.services.task_distributor import TaskDistributor
from src.services.message_cascade import MessageCascade


# ─── Adres Sistemi Testleri ──────────────────────────────────────────────────

class TestNodeAddress:
    def test_root(self):
        root = NodeAddress.root()
        assert root.level == 0
        assert root.indices == []
        assert root.to_string() == "L0"
    
    def test_from_string(self):
        addr = NodeAddress.from_string("L3.0.4.7")
        assert addr.level == 3
        assert addr.indices == [0, 4, 7]
    
    def test_to_path(self):
        addr = NodeAddress.from_string("L3.0.4.7")
        assert addr.to_path() == "0/4/7"
    
    def test_parent(self):
        addr = NodeAddress.from_string("L3.0.4.7")
        parent = addr.parent
        assert parent.to_string() == "L2.0.4"
    
    def test_root_has_no_parent(self):
        root = NodeAddress.root()
        assert root.parent is None
    
    def test_child(self):
        addr = NodeAddress.from_string("L2.0.4")
        child = addr.child(7)
        assert child.to_string() == "L3.0.4.7"
    
    def test_children_count(self):
        addr = NodeAddress.from_string("L1.3")
        children = addr.children
        assert len(children) == 10
    
    def test_siblings(self):
        addr = NodeAddress.from_string("L1.3")
        siblings = addr.siblings
        assert len(siblings) == 9
        assert addr not in siblings
    
    def test_is_ancestor(self):
        ancestor = NodeAddress.from_string("L1.3")
        descendant = NodeAddress.from_string("L3.3.7.2")
        assert ancestor.is_ancestor_of(descendant)
        assert not descendant.is_ancestor_of(ancestor)
    
    def test_common_ancestor(self):
        a = NodeAddress.from_string("L3.0.4.7")
        b = NodeAddress.from_string("L3.0.4.2")
        common = a.common_ancestor(b)
        assert common.to_string() == "L2.0.4"
    
    def test_subtree_size(self):
        root = NodeAddress.root()
        # 10^0 + 10^1 + ... + 10^10 = 11,111,111,111
        assert root.subtree_size == 11111111111
    
    def test_level_1_subtree(self):
        addr = NodeAddress.from_string("L1.0")
        # 10^0 + 10^1 + ... + 10^9 = 1,111,111,111
        assert addr.subtree_size == 1111111111


# ─── Koordinasyon Motoru Testleri ────────────────────────────────────────────

class TestCoordinationEngine:
    @pytest.fixture
    def engine(self):
        return CoordinationEngine()
    
    @pytest.mark.asyncio
    async def test_register_node(self, engine):
        node = await engine.register_node("L0", name="Kök")
        assert node.address.to_string() == "L0"
        assert "L0" in engine.nodes
    
    @pytest.mark.asyncio
    async def test_register_child_auto_creates_parent(self, engine):
        await engine.register_node("L0")
        await engine.register_node("L1.3")
        assert "L1.3" in engine.nodes
    
    @pytest.mark.asyncio
    async def test_heartbeat(self, engine):
        await engine.register_node("L0")
        result = await engine.heartbeat("L0")
        assert result["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_find_least_loaded(self, engine):
        await engine.register_node("L0")
        for i in range(10):
            node = await engine.register_node(f"L1.{i}")
            node.current_load = i * 10  # 0, 10, 20, ..., 90
        
        least = await engine.find_least_loaded_child("L0")
        assert least == "L1.0"
    
    @pytest.mark.asyncio
    async def test_system_overview(self, engine):
        await engine.register_node("L0")
        for i in range(10):
            await engine.register_node(f"L1.{i}")
        
        overview = engine.get_system_overview()
        assert overview["total_registered_nodes"] == 11
        assert overview["active_nodes"] == 11


# ─── Görev Dağıtım Testleri ─────────────────────────────────────────────────

class TestTaskDistributor:
    @pytest_asyncio.fixture
    async def setup(self):
        engine = CoordinationEngine()
        task_dist = TaskDistributor(engine)
        
        # 2 seviye kaydet
        await engine.register_node("L0", name="Kök")
        for i in range(10):
            await engine.register_node(f"L1.{i}")
            for j in range(10):
                await engine.register_node(f"L2.{i}.{j}")
        
        return engine, task_dist
    
    @pytest.mark.asyncio
    async def test_create_task(self, setup):
        engine, task_dist = setup
        task = await task_dist.create_task(
            title="Test Görevi",
            created_by="L0",
        )
        assert task.task_uid.startswith("T-")
        assert task.status == "pending"
    
    @pytest.mark.asyncio
    async def test_cascade_distribution(self, setup):
        engine, task_dist = setup
        task = await task_dist.create_task(
            title="Kademeli Görev",
            created_by="L0",
            assigned_to="L0",
            target_level=2,
            strategy="cascade",
        )
        
        # L0 → 10 alt görev (L1) → her biri 10 alt görev (L2) = 110+1
        assert len(task.subtask_uids) == 10
        assert task.status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_complete_propagation(self, setup):
        engine, task_dist = setup
        parent = await task_dist.create_task(
            title="Ana",
            created_by="L0",
            assigned_to="L0",
            target_level=1,
            strategy="cascade",
        )
        
        # Tüm alt görevleri tamamla
        for sub_uid in parent.subtask_uids:
            await task_dist.complete_task(sub_uid)
        
        assert parent.status == "completed"
        assert parent.progress_pct == 100.0


# ─── Mesajlaşma Testleri ────────────────────────────────────────────────────

class TestMessageCascade:
    @pytest_asyncio.fixture
    async def setup(self):
        engine = CoordinationEngine()
        msg_cascade = MessageCascade(engine)
        
        await engine.register_node("L0")
        for i in range(10):
            await engine.register_node(f"L1.{i}")
            for j in range(10):
                await engine.register_node(f"L2.{i}.{j}")
        
        return engine, msg_cascade
    
    @pytest.mark.asyncio
    async def test_send_directive(self, setup):
        engine, msg_cascade = setup
        msg = await msg_cascade.send_directive(
            sender="L0",
            subject="Test Emri",
            target_depth=1,
        )
        assert msg.cascade_reached == 10  # 10 çocuğa ulaştı
    
    @pytest.mark.asyncio
    async def test_send_directive_depth_2(self, setup):
        engine, msg_cascade = setup
        msg = await msg_cascade.send_directive(
            sender="L0",
            subject="Derin Emir",
            target_depth=2,
        )
        assert msg.cascade_reached == 110  # 10 + 100
    
    @pytest.mark.asyncio
    async def test_send_report(self, setup):
        engine, msg_cascade = setup
        msg = await msg_cascade.send_report(
            sender="L2.0.5",
            subject="Rapor",
            data={"completed": 42},
        )
        assert msg.cascade_reached == 1  # Ebeveyne ulaştı
    
    @pytest.mark.asyncio
    async def test_escalation(self, setup):
        engine, msg_cascade = setup
        msg = await msg_cascade.send_report(
            sender="L2.3.7",
            subject="Acil Sorun",
            escalate=True,
        )
        assert msg.cascade_reached == 2  # L1.3 ve L0'a ulaştı
    
    @pytest.mark.asyncio
    async def test_inbox(self, setup):
        engine, msg_cascade = setup
        await msg_cascade.send_directive(
            sender="L0",
            subject="Kontrol",
            target_depth=1,
        )
        
        inbox = msg_cascade.get_inbox("L1.0")
        assert len(inbox) == 1
        assert inbox[0].subject == "Kontrol"


# ─── Mesaj Entegrasyon Testleri ──────────────────────────────────────────────

class TestMessageIntegration:
    """MessageCascade ↔ CoordinationEngine entegrasyon testleri"""
    
    @pytest_asyncio.fixture
    async def setup(self):
        engine = CoordinationEngine()
        task_dist = TaskDistributor(engine)
        msg_cascade = MessageCascade(engine)
        
        # Servisleri bağla
        engine.set_message_cascade(msg_cascade)
        engine.set_task_distributor(task_dist)
        
        # 2 seviye oluştur
        await engine.register_node("L0")
        for i in range(10):
            await engine.register_node(f"L1.{i}")
            for j in range(10):
                await engine.register_node(f"L2.{i}.{j}")
        
        return engine, task_dist, msg_cascade
    
    @pytest.mark.asyncio
    async def test_pending_messages_count(self, setup):
        """_get_pending_messages artık gerçek unread sayısını döner"""
        engine, task_dist, msg_cascade = setup
        
        # Önce: 0 mesaj
        count = await engine._get_pending_messages("L1.0")
        assert count == 0
        
        # Mesaj gönder
        await msg_cascade.send_directive(sender="L0", subject="Test", target_depth=1)
        
        # Sonra: 1 okunmamış mesaj
        count = await engine._get_pending_messages("L1.0")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_pending_tasks_count(self, setup):
        """_get_pending_tasks artık gerçek pending sayısını döner"""
        engine, task_dist, msg_cascade = setup
        
        # targeted strateji: görev sadece atanır, cascade yapılmaz
        await task_dist.create_task(
            title="Test Görevi",
            created_by="L0",
            assigned_to="L1.0",
            strategy="targeted",
        )
        
        count = await engine._get_pending_tasks("L1.0")
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_heartbeat_returns_real_counts(self, setup):
        """Heartbeat artık gerçek pending mesaj/görev sayılarını döner"""
        engine, task_dist, msg_cascade = setup
        
        # Mesaj ve görev oluştur
        await msg_cascade.send_directive(sender="L0", subject="Emir", target_depth=1)
        await task_dist.create_task(
            title="Görev",
            created_by="L0",
            assigned_to="L1.0",
            strategy="targeted",
        )
        
        result = await engine.heartbeat("L1.0")
        assert result["pending_messages"] >= 1
        assert result["pending_tasks"] >= 1
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, setup):
        """Mesaj okundu işaretleme"""
        engine, task_dist, msg_cascade = setup
        
        msg = await msg_cascade.send_directive(
            sender="L0", subject="Oku beni", target_depth=1
        )
        
        # Okunmamış = 1
        assert msg_cascade.get_unread_count("L1.0") == 1
        
        # Okundu işaretle
        inbox = msg_cascade.get_inbox("L1.0")
        result = msg_cascade.mark_as_read("L1.0", inbox[0].message_uid)
        assert result is True
        
        # Artık okunmamış = 0
        assert msg_cascade.get_unread_count("L1.0") == 0
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, setup):
        """Tüm mesajları okundu işaretleme"""
        engine, task_dist, msg_cascade = setup
        
        # 2 mesaj gönder
        await msg_cascade.send_directive(sender="L0", subject="Bir", target_depth=1)
        await msg_cascade.send_directive(sender="L0", subject="İki", target_depth=1)
        
        assert msg_cascade.get_unread_count("L1.0") == 2
        
        count = msg_cascade.mark_all_as_read("L1.0")
        assert count == 2
        assert msg_cascade.get_unread_count("L1.0") == 0
    
    @pytest.mark.asyncio
    async def test_unread_only_filter(self, setup):
        """get_inbox unread_only filtresi"""
        engine, task_dist, msg_cascade = setup
        
        await msg_cascade.send_directive(sender="L0", subject="Mesaj1", target_depth=1)
        await msg_cascade.send_directive(sender="L0", subject="Mesaj2", target_depth=1)
        
        # Birini oku
        inbox = msg_cascade.get_inbox("L1.0")
        msg_cascade.mark_as_read("L1.0", inbox[0].message_uid)
        
        # Tümü: 2, okunmamış: 1
        assert len(msg_cascade.get_inbox("L1.0")) == 2
        assert len(msg_cascade.get_inbox("L1.0", unread_only=True)) == 1
    
    @pytest.mark.asyncio
    async def test_delete_message(self, setup):
        """Mesaj silme"""
        engine, task_dist, msg_cascade = setup
        
        await msg_cascade.send_directive(sender="L0", subject="Sil beni", target_depth=1)
        inbox = msg_cascade.get_inbox("L1.0")
        uid = inbox[0].message_uid
        
        result = msg_cascade.delete_message("L1.0", uid)
        assert result is True
        assert len(msg_cascade.get_inbox("L1.0")) == 0
    
    @pytest.mark.asyncio
    async def test_peer_message(self, setup):
        """Eşler arası mesaj"""
        engine, task_dist, msg_cascade = setup
        
        msg = await msg_cascade.send_peer_message(
            sender="L1.0",
            recipient="L1.5",
            subject="Selam",
            body="Nasılsın?",
        )
        
        assert msg.message_type == "peer"
        assert msg.cascade_reached == 1
        
        inbox = msg_cascade.get_inbox("L1.5")
        assert len(inbox) == 1
        assert inbox[0].subject == "Selam"
    
    @pytest.mark.asyncio
    async def test_node_message_stats(self, setup):
        """Düğüm mesaj istatistikleri"""
        engine, task_dist, msg_cascade = setup
        
        await msg_cascade.send_directive(sender="L0", subject="Emir", target_depth=1)
        await msg_cascade.send_peer_message(
            sender="L1.0", recipient="L1.5", subject="Peer"
        )
        
        stats = msg_cascade.get_node_message_stats("L1.0")
        assert stats["total_inbox"] == 1  # directive aldı
        assert stats["sent_count"] >= 1   # peer gönderdi
        assert stats["unread"] == 1
    
    @pytest.mark.asyncio
    async def test_auto_escalation_on_offline(self, setup):
        """Düğüm offline olunca otomatik eskalasyon"""
        engine, task_dist, msg_cascade = setup
        
        # L1.3'ü offline yap
        await engine.update_node_status("L1.3", "offline")
        
        # L0'ın inbox'ında eskalasyon olmalı
        inbox = msg_cascade.get_inbox("L0")
        escalations = [m for m in inbox if "çevrimdışı" in m.subject]
        assert len(escalations) >= 1
    
    @pytest.mark.asyncio
    async def test_auto_notification_on_recovery(self, setup):
        """Düğüm offline → active olunca bildirim"""
        engine, task_dist, msg_cascade = setup
        
        # Önce offline, sonra active
        await engine.update_node_status("L1.3", "offline")
        await engine.update_node_status("L1.3", "active")
        
        inbox = msg_cascade.get_inbox("L0")
        recovery_msgs = [m for m in inbox if "tekrar aktif" in m.subject]
        assert len(recovery_msgs) >= 1
    
    @pytest.mark.asyncio
    async def test_auto_overload_escalation(self, setup):
        """Yük >%90 olunca otomatik eskalasyon"""
        engine, task_dist, msg_cascade = setup
        
        # L1.5'in yükünü %95'e çıkar
        await engine.update_node_status("L1.5", "active", load=95)
        
        inbox = msg_cascade.get_inbox("L0")
        overload_msgs = [m for m in inbox if "Aşırı yük" in m.subject]
        assert len(overload_msgs) >= 1
    
    @pytest.mark.asyncio
    async def test_global_statistics(self, setup):
        """Sistem geneli mesaj istatistikleri"""
        engine, task_dist, msg_cascade = setup
        
        await msg_cascade.send_directive(sender="L0", subject="Test", target_depth=1)
        
        stats = msg_cascade.get_statistics()
        assert stats["total_messages"] >= 1
        assert stats["total_unread"] >= 10  # 10 düğüme gitti, hepsi okunmamış
        assert "directive" in stats["by_type"]
    
    @pytest.mark.asyncio
    async def test_outbox_tracking(self, setup):
        """Gönderen outbox takibi"""
        engine, task_dist, msg_cascade = setup
        
        await msg_cascade.send_directive(sender="L0", subject="Test", target_depth=1)
        
        outbox = msg_cascade.node_outbox.get("L0", [])
        assert len(outbox) >= 1


# ─── Yardımcı Fonksiyon Testleri ────────────────────────────────────────────

class TestHelpers:
    def test_format_node_count_billion(self):
        assert "Milyar" in format_node_count(9_000_000_000)
    
    def test_format_node_count_million(self):
        assert "Milyon" in format_node_count(5_000_000)
    
    def test_level_summary(self):
        summary = level_summary()
        assert 0 in summary
        assert 10 in summary
        assert summary[0]["node_count"] == 1
        assert summary[1]["node_count"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
