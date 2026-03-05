"""
Hive Coordinator CLI - Komut Satırı Yönetim Aracı
===================================================

Kullanım:
    python -m src.cli overview          # Sistem özeti
    python -m src.cli tree              # Hiyerarşi ağacı
    python -m src.cli simulate          # Demo simülasyonu
    python -m src.cli node L1.3         # Düğüm bilgisi
"""

from __future__ import annotations
import asyncio
import random
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich import box

from src import HIERARCHY_DEPTH, BRANCH_FACTOR
from src.utils.addressing import (
    NodeAddress, level_summary, format_node_count, _level_role
)
from src.services.coordination_engine import CoordinationEngine
from src.services.task_distributor import TaskDistributor
from src.services.message_cascade import MessageCascade

console = Console()


def show_banner():
    """Sistem başlangıç banner'ı"""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     🐝  HIVE COORDINATOR  🐝                                      ║
║     Hiyerarşik Yazılım Ekibi Koordinasyon Sistemi                ║
║                                                                   ║
║     9 Milyar Düğüm  ·  10 Seviye  ·  10'lu Gruplar              ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")


def show_hierarchy_overview():
    """Hiyerarşi seviyelerinin detaylı tablosu"""
    show_banner()
    
    table = Table(
        title="📊 Hiyerarşi Seviyeleri",
        box=box.DOUBLE_EDGE,
        show_lines=True,
        title_style="bold magenta",
    )
    
    table.add_column("Seviye", style="bold cyan", justify="center")
    table.add_column("Rol", style="bold white")
    table.add_column("Düğüm Sayısı", style="green", justify="right")
    table.add_column("Kümülatif", style="yellow", justify="right")
    table.add_column("Alt Ağaç Boyutu", style="blue", justify="right")
    table.add_column("Yayın Adımı", style="red", justify="center")
    
    summary = level_summary()
    for level, info in summary.items():
        subtree_size = sum(10**i for i in range(HIERARCHY_DEPTH - level + 1))
        table.add_row(
            f"L{level}",
            info["role"],
            info["node_count_str"],
            info["cumulative_str"],
            format_node_count(subtree_size),
            f"{level} adım" if level > 0 else "Kök",
        )
    
    console.print(table)
    console.print()
    
    # Özet panel
    total = sum(10**i for i in range(HIERARCHY_DEPTH + 1))
    console.print(Panel(
        f"[bold]Toplam Kapasite:[/bold] {format_node_count(total)} düğüm\n"
        f"[bold]Dallanma Faktörü:[/bold] Her düğüm {BRANCH_FACTOR} çocuk\n"
        f"[bold]Yayın Hızı:[/bold] Kökten yapraklara {HIERARCHY_DEPTH} adımda\n"
        f"[bold]Mesaj Karmaşıklığı:[/bold] O(log₁₀ N) = O({HIERARCHY_DEPTH})\n"
        f"[bold]Her Düğümün Sorumluluğu:[/bold] Max {BRANCH_FACTOR} doğrudan bağlantı",
        title="🔑 Sistem Parametreleri",
        border_style="green",
    ))


def show_tree_view(max_depth: int = 3):
    """Hiyerarşi ağaç görünümü"""
    show_banner()
    
    tree = Tree(
        f"[bold cyan]L0 - Genel Koordinatör[/bold cyan] "
        f"[dim](Alt ağaç: {format_node_count(sum(10**i for i in range(11)))})[/dim]"
    )
    
    def add_children(parent_tree, parent_addr: NodeAddress, depth: int):
        if depth >= max_depth:
            remaining = HIERARCHY_DEPTH - parent_addr.level - 1
            if remaining > 0:
                total_below = sum(10**i for i in range(1, remaining + 1))
                parent_tree.add(
                    f"[dim]... {BRANCH_FACTOR} dal × "
                    f"{format_node_count(total_below)} düğüm ...[/dim]"
                )
            return
        
        for i in range(BRANCH_FACTOR):
            child = parent_addr.child(i)
            role = _level_role(child.level)
            subtree = sum(10**j for j in range(HIERARCHY_DEPTH - child.level + 1))
            
            style = "green" if i < 3 else "yellow" if i < 7 else "red"
            child_tree = parent_tree.add(
                f"[{style}]{child.to_string()}[/{style}] - {role} "
                f"[dim]({format_node_count(subtree)} düğüm)[/dim]"
            )
            
            add_children(child_tree, child, depth + 1)
    
    root = NodeAddress.root()
    add_children(tree, root, 0)
    
    console.print(tree)


def run_simulation():
    """
    Tam bir simülasyon çalıştır:
    1. Düğümleri kaydet
    2. Görev oluştur ve dağıt
    3. Mesaj yay
    4. Durumları topla
    """
    show_banner()
    console.print("[bold yellow]🚀 Simülasyon Başlatılıyor...[/bold yellow]\n")
    
    async def _simulate():
        engine = CoordinationEngine()
        task_dist = TaskDistributor(engine)
        msg_cascade = MessageCascade(engine)
        
        # 1. DÜĞÜM KAYDI
        console.print("[bold cyan]━━━ ADIM 1: Düğüm Kaydı ━━━[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Düğümler kaydediliyor...", total=None)
            
            registered = 0
            # İlk 3 seviyeyi kaydet (111 düğüm)
            for level in range(4):
                if level == 0:
                    await engine.register_node("L0", name="Genel Koordinatör")
                    registered += 1
                else:
                    # Belirli dalları kaydet
                    addresses = _generate_addresses(level, sample_count=min(10**level, 10**level))
                    for addr in addresses:
                        await engine.register_node(
                            addr,
                            name=_level_role(level),
                            capacity=random.randint(80, 120),
                            efficiency=round(random.uniform(0.7, 1.3), 2),
                        )
                        registered += 1
            
            progress.update(task, description=f"✅ {registered} düğüm kaydedildi")
        
        console.print(f"   Kayıtlı düğümler: [green]{registered}[/green]")
        console.print(f"   Temsil ettikleri: [green]{format_node_count(sum(10**i for i in range(11)))}[/green] düğüm")
        console.print()
        
        # 2. YÜK ATAMA
        console.print("[bold cyan]━━━ ADIM 2: Yük Simülasyonu ━━━[/bold cyan]")
        for addr, node in engine.nodes.items():
            node.current_load = random.randint(10, 90)
        
        overview = engine.get_system_overview()
        console.print(f"   Ortalama yük: [yellow]%{overview['avg_load_pct']}[/yellow]")
        console.print()
        
        # 3. GÖREV DAĞITIMI
        console.print("[bold cyan]━━━ ADIM 3: Görev Dağıtımı ━━━[/bold cyan]")
        
        main_task = await task_dist.create_task(
            title="Küresel Yazılım Projesi v2.0",
            description="9 milyar geliştiricinin koordineli çalıştığı mega proje",
            priority="critical",
            created_by="L0",
            assigned_to="L0",
            target_level=3,
            strategy="cascade",
        )
        
        task_stats = task_dist.get_statistics()
        console.print(f"   Ana görev: [green]{main_task.title}[/green]")
        console.print(f"   Oluşturulan alt görevler: [green]{task_stats['total_tasks']}[/green]")
        console.print(f"   Durum dağılımı: {task_stats['by_status']}")
        console.print()
        
        # Görev ağacını göster
        tree_view = task_dist.get_task_tree(main_task.task_uid, max_depth=2)
        _print_task_tree(tree_view)
        console.print()
        
        # 4. MESAJLAŞMA
        console.print("[bold cyan]━━━ ADIM 4: Kademeli Mesajlaşma ━━━[/bold cyan]")
        
        # Yukarıdan aşağı emir
        directive = await msg_cascade.send_directive(
            sender="L0",
            subject="Sprint 47 Başlangıcı",
            body="Tüm takımlar yeni sprint hedeflerine odaklansın.",
            target_depth=3,
            priority="high",
        )
        console.print(f"   📤 Emir gönderildi: '{directive.subject}'")
        console.print(f"      Ulaşılan düğüm: [green]{directive.cascade_reached}[/green]")
        
        # Yayın
        broadcast = await msg_cascade.send_broadcast(
            sender="L0",
            subject="Sistem Bakım Bildirimi",
            body="Yarın 02:00-04:00 arası planlı bakım yapılacaktır.",
        )
        console.print(f"   📢 Yayın gönderildi: '{broadcast.subject}'")
        console.print(f"      Ulaşılan düğüm: [green]{broadcast.cascade_reached}[/green]")
        
        # Rapor (aşağıdan yukarı)
        report = await msg_cascade.send_report(
            sender="L3.0.4.7",
            subject="Sprint İlerleme Raporu",
            body="Takım performansı hedefin %15 üzerinde.",
            data={"completed_tasks": 47, "velocity": 115},
        )
        console.print(f"   📝 Rapor gönderildi: '{report.subject}'")
        console.print(f"      Üste iletildi: [green]{report.cascade_reached}[/green] seviye")
        
        # Eskalasyon
        escalation = await msg_cascade.send_report(
            sender="L3.2.8.1",
            subject="KRİTİK: Veritabanı Erişim Sorunu",
            body="Bölge 2-8-1'deki tüm geliştirici DB'ye erişemiyor.",
            escalate=True,
        )
        console.print(f"   🚨 Eskalasyon: '{escalation.subject}'")
        console.print(f"      Köke kadar iletildi: [red]{escalation.cascade_reached}[/red] seviye")
        
        msg_stats = msg_cascade.get_statistics()
        console.print(f"\n   Toplam mesaj: {msg_stats['total_messages']}")
        console.print(f"   Toplam teslimat: {msg_stats['total_deliveries']}")
        console.print()
        
        # 5. SAĞLIK KONTROLÜ
        console.print("[bold cyan]━━━ ADIM 5: Sağlık Kontrolü ━━━[/bold cyan]")
        
        # Bazı düğümleri "sorunlu" yap
        for addr in random.sample(list(engine.nodes.keys()), min(3, len(engine.nodes))):
            if addr != "L0":
                engine.nodes[addr].status = "offline"
        
        health = await engine.health_check("L0")
        console.print(f"   Kök sağlık: [{'green' if health['healthy'] else 'red'}]"
                      f"{'Sağlıklı' if health['healthy'] else 'Sorunlu'}[/]")
        console.print(f"   Tespit edilen sorunlar: [yellow]{len(health['issues'])}[/yellow]")
        for issue in health['issues'][:5]:
            console.print(f"      ⚠️  {issue}")
        console.print()
        
        # 6. YÜK DENGELEME
        console.print("[bold cyan]━━━ ADIM 6: Yük Dengeleme ━━━[/bold cyan]")
        
        transfers = await engine.rebalance_subtree("L0")
        if transfers:
            console.print(f"   Yük transferleri: [green]{len(transfers)}[/green]")
            for t in transfers[:5]:
                console.print(f"      {t['from']} → {t['to']}: {t['amount']} birim")
        else:
            console.print("   Yük dengeli, transfer gerekmedi.")
        console.print()
        
        # 7. GÖREV TAMAMLAMA
        console.print("[bold cyan]━━━ ADIM 7: Görev Tamamlama Simülasyonu ━━━[/bold cyan]")
        
        # Yaprak görevleri tamamla
        leaf_tasks = [t for t in task_dist.tasks.values() if t.is_leaf and t.status != "completed"]
        completed_count = 0
        for task in random.sample(leaf_tasks, min(len(leaf_tasks), len(leaf_tasks) // 2 + 1)):
            result = await task_dist.complete_task(task.task_uid)
            completed_count += 1
            if result.get("propagation"):
                console.print(f"   ✅ {task.task_uid}: propagation → {result['propagation']}")
        
        console.print(f"   Tamamlanan görevler: [green]{completed_count}[/green]")
        
        # Ana görev durumu
        main = task_dist.tasks[main_task.task_uid]
        console.print(f"   Ana görev ilerlemesi: [{'green' if main.progress_pct == 100 else 'yellow'}]"
                      f"%{main.progress_pct:.0f}[/]")
        console.print()
        
        # ─── ÖZET ────────────────────────────────────────────────────────
        console.print(Panel(
            f"[bold]Kayıtlı Düğümler:[/bold] {len(engine.nodes)}\n"
            f"[bold]Toplam Görevler:[/bold] {len(task_dist.tasks)}\n"
            f"[bold]Toplam Mesajlar:[/bold] {len(msg_cascade.messages)}\n"
            f"[bold]Mesaj Teslimatları:[/bold] {msg_stats['total_deliveries']}\n"
            f"[bold]Yük Transferleri:[/bold] {len(transfers) if transfers else 0}\n"
            f"[bold]Ana Görev İlerlemesi:[/bold] %{main.progress_pct:.0f}",
            title="📊 Simülasyon Özeti",
            border_style="green",
        ))
    
    asyncio.run(_simulate())


def _generate_addresses(level: int, sample_count: int = None) -> list[str]:
    """Belirli bir seviye için tüm adresleri üret"""
    if level == 0:
        return ["L0"]
    
    addresses = []
    
    def _recurse(indices: list[int], remaining: int):
        if remaining == 0:
            addr = f"L{level}." + ".".join(str(i) for i in indices)
            addresses.append(addr)
            return
        for i in range(BRANCH_FACTOR):
            _recurse(indices + [i], remaining - 1)
            if sample_count and len(addresses) >= sample_count:
                return
    
    _recurse([], level)
    return addresses[:sample_count] if sample_count else addresses


def _print_task_tree(tree_data: dict, indent: int = 0):
    """Görev ağacını konsola yazdır"""
    if not tree_data:
        return
    
    prefix = "   " + "  │ " * indent
    status_icon = {
        "completed": "✅",
        "in_progress": "🔄",
        "pending": "⏳",
        "assigned": "📋",
        "failed": "❌",
        "blocked": "🚫",
    }
    
    icon = status_icon.get(tree_data.get("status", ""), "❓")
    console.print(
        f"{prefix}{icon} {tree_data['uid'][:15]}... "
        f"[dim]{tree_data.get('title', '')[:40]}[/dim] "
        f"→ {tree_data.get('assigned_to', 'N/A')} "
        f"[{'green' if tree_data.get('progress_pct', 0) == 100 else 'yellow'}]"
        f"%{tree_data.get('progress_pct', 0):.0f}[/]"
    )
    
    for subtask in tree_data.get("subtasks", []):
        _print_task_tree(subtask, indent + 1)


# ─── Ana Giriş Noktası ──────────────────────────────────────────────────────

def main():
    """CLI ana fonksiyonu"""
    import sys
    
    if len(sys.argv) < 2:
        show_hierarchy_overview()
        return
    
    command = sys.argv[1].lower()
    
    if command == "overview":
        show_hierarchy_overview()
    elif command == "tree":
        depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        show_tree_view(max_depth=depth)
    elif command == "simulate" or command == "sim":
        run_simulation()
    elif command == "serve" or command == "api":
        import uvicorn
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        console.print(f"[bold green]🚀 API sunucusu başlatılıyor: http://localhost:{port}[/bold green]")
        console.print(f"[dim]Swagger UI: http://localhost:{port}/docs[/dim]")
        uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)
    else:
        console.print(f"[red]Bilinmeyen komut: {command}[/red]")
        console.print("\nKullanım:")
        console.print("  python -m src.cli overview    Sistem özeti")
        console.print("  python -m src.cli tree [N]    Hiyerarşi ağacı (derinlik N)")
        console.print("  python -m src.cli simulate    Demo simülasyonu")
        console.print("  python -m src.cli serve [P]   API sunucusu (port P)")


if __name__ == "__main__":
    main()


app = main  # Typer uyumluluğu için
