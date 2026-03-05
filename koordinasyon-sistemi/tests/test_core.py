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
