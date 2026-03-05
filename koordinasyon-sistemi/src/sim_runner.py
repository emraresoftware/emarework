"""
1 Yıllık Simülasyon CLI Çıktısı
================================

100GB kod projesinin 100 geliştiriciyle 365 günlük simülasyonunu
zengin terminal çıktısıyla gösterir.

Kullanım:
    python3 -m src.sim_runner
    python3 -m src.sim_runner --fast           # Hızlı mod
    python3 -m src.sim_runner --seed 123       # Farklı seed
    python3 -m src.sim_runner --size 50        # 50 GB proje
    python3 -m src.sim_runner --devs 200       # 200 geliştirici
    python3 -m src.sim_runner --daily-gb 0.5   # Kişi başı 0.5 GB/gün
"""

from __future__ import annotations
import sys
import time
from datetime import date

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress, BarColumn, TextColumn, TimeRemainingColumn, 
    SpinnerColumn, TaskProgressColumn
)
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

from src.services.year_simulation import (
    YearSimulation, DailySnapshot, TOTAL_CODE_KB, SIMULATION_DAYS,
    TOTAL_DEVELOPERS, BRANCH_FACTOR, HIERARCHY_DEPTH, SPRINT_DAYS,
    SKILL_LEVELS, DAILY_TARGET_KB
)

console = Console()


def format_kb(kb: float) -> str:
    """KB'ı okunabilir formata çevir"""
    if kb >= 1024 * 1024 * 1024:
        return f"{kb / (1024 * 1024 * 1024):.2f} TB"
    elif kb >= 1024 * 1024:
        return f"{kb / (1024 * 1024):.2f} GB"
    elif kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb:.0f} KB"


def format_num(n: int) -> str:
    """Sayıyı binlik ayraçla formatla"""
    return f"{n:,}".replace(",", ".")


def run_simulation(size_gb: float = 100, seed: int = 42, fast: bool = False,
                   num_devs: int = 100, daily_gb: float = 1.0):
    """Ana simülasyon çalıştırıcı"""
    
    total_kb = int(size_gb * 1024 * 1024)
    daily_per_dev_kb = int(daily_gb * 1024 * 1024)
    
    # Hiyerarşi hesapla
    import math
    depth = max(1, int(math.log(num_devs, BRANCH_FACTOR)))
    
    # ═════════════════════════════════════════════════════════════════════
    # BAŞLANGIÇ EKRANI
    # ═════════════════════════════════════════════════════════════════════
    
    daily_per_dev_str = format_kb(daily_per_dev_kb)
    yearly_per_dev_str = format_kb(daily_per_dev_kb * SIMULATION_DAYS)
    size_str = f"{size_gb/1024:.1f} TB" if size_gb >= 1024 else f"{size_gb:.1f} GB"
    
    banner = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🐝  HIVE COORDINATOR - 1 YILLIK PROJE SİMÜLASYONU  🐝             ║
║                                                                      ║
║   Proje Boyutu:    {size_str:>12}                                     ║
║   Geliştirici:     {num_devs:>8,} kişi ({depth+1} seviye hiyerarşi)          ║
║   Süre:            {SIMULATION_DAYS:>8} gün (52 sprint × 7 gün)            ║
║   Kişi Başı/Gün:  {daily_per_dev_str:>10}                                   ║
║   Kişi Başı/Yıl:  {yearly_per_dev_str:>10}                                  ║
║   Seed:            {seed:>8}                                         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")
    
    # Ekip yapısı özeti
    _show_team_overview(num_devs, depth)
    
    # ═════════════════════════════════════════════════════════════════════
    # SİMÜLASYON
    # ═════════════════════════════════════════════════════════════════════
    
    sim = YearSimulation(
        total_code_kb=total_kb,
        num_developers=num_devs,
        daily_per_dev_kb=daily_per_dev_kb,
        seed=seed,
    )
    
    console.print("\n[bold yellow]🚀 Simülasyon başlıyor...[/bold yellow]\n")
    
    last_sprint = 0
    sprint_summaries = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("•"),
        TextColumn("[green]{task.fields[produced]}[/green]"),
        TextColumn("•"),
        TextColumn("[yellow]{task.fields[progress_pct]}[/yellow]"),
        console=console,
    ) as progress:
        
        task = progress.add_task(
            "Simülasyon", total=SIMULATION_DAYS,
            produced="0 KB", progress_pct="0%",
        )
        
        def on_progress(day: int, snapshot: DailySnapshot):
            nonlocal last_sprint
            
            progress.update(
                task, completed=day,
                description=f"Gün {day:>3}/365 | {snapshot.date}",
                produced=format_kb(snapshot.cumulative_code_kb),
                progress_pct=f"%{snapshot.progress_pct:.1f}",
            )
            
            # Sprint sonu çıktısı
            current_sprint = (day - 1) // SPRINT_DAYS + 1
            if current_sprint > last_sprint and not fast:
                last_sprint = current_sprint
                if len(sim.sprint_reports) > 0:
                    sr = sim.sprint_reports[-1]
                    sprint_summaries.append(sr)
            
            if not fast:
                time.sleep(0.002)  # Görsel efekt
        
        result = sim.run(progress_callback=on_progress)
    
    # ═════════════════════════════════════════════════════════════════════
    # SONUÇLAR
    # ═════════════════════════════════════════════════════════════════════
    
    console.print("\n")
    console.print("=" * 72, style="bold cyan")
    console.print("  📊  SİMÜLASYON SONUÇLARI - YIL SONU RAPORU", style="bold cyan")
    console.print("=" * 72, style="bold cyan")
    console.print()
    
    # 1. Üretim Özeti
    _show_production_summary(result)
    
    # 2. Kalite Metrikleri
    _show_quality_metrics(result)
    
    # 3. Sprint Performansı
    _show_sprint_performance(sim.sprint_reports)
    
    # 4. Aylık Trend
    _show_monthly_trend(result)
    
    # 5. Geliştirici Performansı
    _show_developer_stats(result)
    
    # 6. İletişim İstatistikleri
    _show_communication_stats(result)
    
    # 7. Olay Özeti
    _show_event_summary(result)
    
    # 8. En Önemli Olaylar (son 3 sprint)
    _show_notable_events(sim.sprint_reports[-3:] if len(sim.sprint_reports) >= 3 else sim.sprint_reports)
    
    # 9. Bellek Kullanımı
    _show_memory_usage(sim)
    
    # Final
    console.print("\n")
    completed = result["production"]["completion_pct"]
    produced_str = format_kb(result['production']['total_code_produced_kb'])
    target_str = format_kb(total_kb)
    if completed >= 100:
        console.print(Panel(
            f"[bold green]✅ PROJE TAMAMLANDI![/bold green]\n\n"
            f"Hedef: {target_str} → Üretilen: {produced_str}\n"
            f"Tamamlanma: %{completed:.1f}\n"
            f"Toplam Mesaj: {format_num(result['communication']['total_messages'])}",
            title="🎉 Başarı", border_style="green",
        ))
    else:
        remaining_kb = total_kb - result['production']['total_code_produced_kb']
        remaining_str = format_kb(remaining_kb)
        daily_prod_kb = result['production']['avg_daily_production_kb']
        est_days = remaining_kb / max(0.001, daily_prod_kb)
        console.print(Panel(
            f"[bold yellow]⏳ PROJE DEVAM EDİYOR[/bold yellow]\n\n"
            f"Hedef: {target_str} → Üretilen: {produced_str}\n"
            f"Tamamlanma: %{completed:.1f} | Kalan: {remaining_str}\n"
            f"Tahmini Kalan Süre: {est_days:.0f} gün",
            title="📋 Durum", border_style="yellow",
        ))


def _show_team_overview(num_devs: int = 100, depth: int = 2):
    """Ekip yapısı tablosu"""
    table = Table(title="👥 Ekip Yapısı", box=box.ROUNDED)
    table.add_column("Seviye", style="cyan")
    table.add_column("Rol", style="white")
    table.add_column("Kişi Sayısı", style="green", justify="right")
    table.add_column("Görev", style="dim")
    
    role_names = {
        0: ("Genel Koordinatör", "Proje yönetimi, strateji"),
        1: ("Takım Lideri", "Modül denetimi, sprint planlama"),
        2: ("Geliştirici", "Kod üretimi, bug fix, test"),
        3: ("Geliştirici", "Kod üretimi, bug fix, test"),
    }
    
    # Yönetim katmanları
    for level in range(depth):
        count = BRANCH_FACTOR ** level
        role, duty = role_names.get(level, ("Yönetici", "Koordinasyon"))
        table.add_row(f"L{level}", role, str(count), duty)
    
    # Geliştirici katmanı
    table.add_row(f"L{depth}", "Geliştirici", str(num_devs), "Kod üretimi, bug fix, test")
    
    console.print(table)
    
    # Yetenek dağılımı
    skill_table = Table(title=f"🎯 Yetenek Dağılımı (L{depth} — {num_devs} kişi)", box=box.SIMPLE)
    skill_table.add_column("Seviye", style="bold")
    skill_table.add_column("Oran", justify="center")
    skill_table.add_column("Hız Çarpanı", justify="center")
    skill_table.add_column("Bug Oranı", justify="center")
    skill_table.add_column("Review Kalitesi", justify="center")
    
    colors = {"junior": "red", "mid": "yellow", "senior": "green", "principal": "cyan"}
    for skill, info in SKILL_LEVELS.items():
        c = colors[skill]
        skill_table.add_row(
            f"[{c}]{skill.capitalize()}[/{c}]",
            f"%{info['ratio']*100:.0f}",
            f"×{info['speed_mult']:.1f}",
            f"%{info['bug_rate']*100:.1f}",
            f"%{info['review_quality']*100:.0f}",
        )
    
    console.print(skill_table)


def _show_production_summary(result: dict):
    """Üretim özeti"""
    p = result["production"]
    
    table = Table(title="📦 Üretim Özeti", box=box.DOUBLE_EDGE, show_lines=True)
    table.add_column("Metrik", style="bold")
    table.add_column("Değer", style="green", justify="right")
    
    completion = p["completion_pct"]
    comp_style = "green" if completion >= 100 else "yellow" if completion >= 80 else "red"
    
    table.add_row("Hedef", format_kb(p['target_kb']))
    table.add_row("Üretilen Kod", format_kb(p['total_code_produced_kb']))
    table.add_row(f"Tamamlanma", f"[{comp_style}]%{completion:.1f}[/{comp_style}]")
    table.add_row("Günlük Üretim (ort.)", format_kb(p['avg_daily_production_kb']))
    table.add_row("Kişi Başı Günlük (ort.)", format_kb(p['avg_daily_per_dev_kb']))
    table.add_row("Kişi Başı Yıllık", format_kb(p['avg_daily_per_dev_kb'] * SIMULATION_DAYS))
    
    console.print(table)
    console.print()


def _show_quality_metrics(result: dict):
    """Kalite metrikleri"""
    q = result["quality"]
    
    table = Table(title="🐛 Kalite Metrikleri", box=box.ROUNDED)
    table.add_column("Metrik", style="bold")
    table.add_column("Değer", justify="right")
    
    open_bugs = q["open_bugs"]
    bug_style = "green" if open_bugs < 100 else "yellow" if open_bugs < 500 else "red"
    
    table.add_row("Toplam Bug Oluşan", f"[red]{format_num(q['total_bugs_created'])}[/red]")
    table.add_row("Düzeltilen Bug", f"[green]{format_num(q['total_bugs_fixed'])}[/green]")
    table.add_row("Açık Bug", f"[{bug_style}]{format_num(open_bugs)}[/{bug_style}]")
    table.add_row("Bug Oranı", f"{q['bug_rate_per_1000kb']:.2f} / 1000 KB")
    table.add_row("Düzeltme Oranı", f"%{q['fix_rate_pct']:.1f}")
    
    console.print(table)
    console.print()


def _show_sprint_performance(sprints: list):
    """Sprint performans tablosu"""
    table = Table(title="🏃 Sprint Performansı (52 Sprint)", box=box.SIMPLE_HEAVY)
    table.add_column("Sprint", style="cyan", justify="center")
    table.add_column("Üretim", justify="right")
    table.add_column("Hedef %", justify="center")
    table.add_column("Bug", justify="center", style="red")
    table.add_column("Fix", justify="center", style="green")
    table.add_column("Aktif Dev", justify="center")
    table.add_column("Kümülatif %", justify="center")
    table.add_column("Mesaj", justify="right", style="dim")
    
    # Her 4 sprintte 1 satır göster (13 satır ≈ çeyrekler)
    for i, sr in enumerate(sprints):
        if i % 4 != 0 and i != len(sprints) - 1:
            continue
        
        pct_style = "green" if sr.plan_completion_pct >= 100 else "yellow" if sr.plan_completion_pct >= 80 else "red"
        cum_style = "green" if sr.cumulative_progress_pct >= (sr.sprint_number / 52) * 100 else "yellow"
        
        table.add_row(
            f"S{sr.sprint_number:>2}",
            format_kb(sr.code_produced_kb),
            f"[{pct_style}]%{sr.plan_completion_pct:.0f}[/{pct_style}]",
            str(sr.bugs_created),
            str(sr.bugs_fixed),
            str(sr.active_developers),
            f"[{cum_style}]%{sr.cumulative_progress_pct:.1f}[/{cum_style}]",
            format_num(sr.total_messages),
        )
    
    console.print(table)
    console.print()


def _show_monthly_trend(result: dict):
    """Aylık trend ASCII grafik"""
    monthly = result.get("monthly_trend", {})
    if not monthly:
        return
    
    console.print("[bold]📈 Aylık Üretim Trendi[/bold]\n")
    
    max_kb = max(m["daily_avg_kb"] for m in monthly.values()) if monthly else 1
    bar_width = 40
    
    for month, data in sorted(monthly.items()):
        ratio = data["daily_avg_kb"] / max_kb
        filled = int(ratio * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        color = "green" if ratio > 0.8 else "yellow" if ratio > 0.6 else "red"
        
        console.print(
            f"  {month}  [{color}]{bar}[/{color}]  "
            f"{format_kb(data['production_gb'] * 1024 * 1024)}  "
            f"(ort: {format_kb(data['daily_avg_kb'])}/gün, "
            f"bug: {data['bugs']})"
        )
    
    console.print()


def _show_developer_stats(result: dict):
    """Geliştirici istatistikleri"""
    
    # Yetenek dağılımı özet
    skill_table = Table(title="👨‍💻 Yetenek Bazlı Performans", box=box.ROUNDED)
    skill_table.add_column("Yetenek", style="bold")
    skill_table.add_column("Kişi", justify="center")
    skill_table.add_column("Toplam Üretim", justify="right")
    skill_table.add_column("Kişi Başı Ort.", justify="right")
    skill_table.add_column("Bug Oluşan", justify="center", style="red")
    skill_table.add_column("Bug Düzeltilen", justify="center", style="green")
    
    for skill, data in result["people"]["skill_distribution"].items():
        if data["count"] == 0:
            continue
        avg_kb = data["total_kb"] / data["count"]
        skill_table.add_row(
            skill.capitalize(),
            str(data["count"]),
            format_kb(data["total_kb"]),
            format_kb(avg_kb),
            format_num(data["bugs_created"]),
            format_num(data["bugs_fixed"]),
        )
    
    console.print(skill_table)
    console.print()
    
    # En iyi 10
    top_table = Table(title="🏆 En Verimli 10 Geliştirici", box=box.SIMPLE)
    top_table.add_column("#", style="bold yellow", justify="center")
    top_table.add_column("Adres", style="cyan")
    top_table.add_column("Yetenek", style="dim")
    top_table.add_column("Üretilen Kod", style="green", justify="right")
    
    for i, dev in enumerate(result["people"]["top_10_producers"], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f" {i}")
        top_table.add_row(
            str(medal), dev["address"], dev["skill"],
            format_kb(dev["produced_kb"]),
        )
    
    console.print(top_table)
    console.print()


def _show_communication_stats(result: dict):
    """İletişim istatistikleri"""
    c = result["communication"]
    
    table = Table(title="💬 İletişim İstatistikleri", box=box.ROUNDED)
    table.add_column("Metrik", style="bold")
    table.add_column("Değer", justify="right")
    
    table.add_row("Toplam Mesaj", format_num(c["total_messages"]))
    table.add_row("Günlük Ortlama", format_num(c["total_messages"] // SIMULATION_DAYS))
    table.add_row("Toplam Olay", format_num(c["total_events"]))
    
    console.print(table)
    console.print()


def _show_event_summary(result: dict):
    """Olay dağılımı"""
    events = result["communication"].get("events_by_type", {})
    if not events:
        return
    
    table = Table(title="📋 Olay Dağılımı (1 Yıl)", box=box.SIMPLE)
    table.add_column("Olay Tipi", style="bold")
    table.add_column("Sayı", justify="right")
    table.add_column("Dağılım", style="dim")
    
    total = sum(events.values())
    
    icons = {
        "status_change": "🔄", "sick": "🤒", "vacation": "🏖️",
        "burnout": "😰", "blocked": "🚫", "breakthrough": "⚡",
        "critical_bug": "🐛", "refactor": "♻️",
    }
    
    for etype, count in sorted(events.items(), key=lambda x: -x[1]):
        icon = icons.get(etype, "📌")
        pct = (count / total * 100) if total > 0 else 0
        bar_len = int(pct / 2)
        bar = "▓" * bar_len
        table.add_row(f"{icon} {etype}", format_num(count), f"{bar} %{pct:.1f}")
    
    console.print(table)
    console.print()


def _show_notable_events(recent_sprints: list):
    """Son sprintlerdeki önemli olaylar"""
    all_events = []
    for sr in recent_sprints:
        all_events.extend(sr.critical_events)
    
    if not all_events:
        return
    
    console.print("[bold]⚠️  Son Sprintlerin Önemli Olayları:[/bold]")
    for event in all_events[:15]:
        console.print(f"  {event}")
    console.print()


def _show_memory_usage(sim: YearSimulation):
    """Simülasyon bellek kullanımı"""
    import sys as _sys
    
    dev_size = _sys.getsizeof(sim.developers) 
    snap_size = _sys.getsizeof(sim.daily_snapshots)
    event_size = _sys.getsizeof(sim.all_events)
    sprint_size = _sys.getsizeof(sim.sprint_reports)
    
    # Tahmini toplam (obj referansları dahil)
    estimated_total_kb = (
        len(sim.developers) * 200 +     # ~200 byte/dev
        len(sim.daily_snapshots) * 150 + # ~150 byte/snapshot
        len(sim.all_events) * 100 +      # ~100 byte/event
        len(sim.sprint_reports) * 300    # ~300 byte/sprint
    ) / 1024
    
    console.print(Panel(
        f"[bold]Düğüm sayısı:[/bold] {format_num(len(sim.developers) + len(sim.teams))}\n"
        f"[bold]Günlük snapshot:[/bold] {len(sim.daily_snapshots)} kayıt\n"
        f"[bold]Sprint raporu:[/bold] {len(sim.sprint_reports)} kayıt\n"
        f"[bold]Olay logu:[/bold] {format_num(len(sim.all_events))} kayıt\n"
        f"[bold]Mesaj sayısı:[/bold] {format_num(sim.cumulative_messages)} (sadece sayaç)\n"
        f"\n[bold]Tahmini Bellek:[/bold] [green]~{estimated_total_kb:.0f} KB ({estimated_total_kb/1024:.1f} MB)[/green]\n"
        f"[dim]Not: 9 milyar düğüme ölçeklense bile mesajlar sadece sayaç olarak\n"
        f"tutulur. Gerçek veri alışverişi kod-bazlı olduğu için minimum yer kaplar.[/dim]",
        title="💾 Simülasyon Bellek Kullanımı",
        border_style="blue",
    ))


# ─── Ana Giriş Noktası ──────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    
    size_gb = 100.0       # 100 GB proje
    seed = 42
    fast = False
    num_devs = 100        # 100 geliştirici
    daily_gb = 1.0        # 1 GB/kişi/gün
    
    i = 0
    while i < len(args):
        if args[i] == "--size" and i + 1 < len(args):
            size_gb = float(args[i + 1])
            i += 2
        elif args[i] == "--seed" and i + 1 < len(args):
            seed = int(args[i + 1])
            i += 2
        elif args[i] == "--devs" and i + 1 < len(args):
            num_devs = int(args[i + 1])
            i += 2
        elif args[i] == "--daily-gb" and i + 1 < len(args):
            daily_gb = float(args[i + 1])
            i += 2
        elif args[i] == "--fast":
            fast = True
            i += 1
        elif args[i] == "--help":
            console.print("[bold]Kullanım:[/bold]")
            console.print("  python3 -m src.sim_runner [--size GB] [--devs N] [--daily-gb GB] [--seed N] [--fast]")
            console.print("\n[bold]Seçenekler:[/bold]")
            console.print("  --size GB      Proje boyutu (varsayılan: 100)")
            console.print("  --devs N       Geliştirici sayısı (varsayılan: 100)")
            console.print("  --daily-gb GB  Kişi başı günlük üretim (varsayılan: 1.0)")
            console.print("  --seed N       Random seed (varsayılan: 42)")
            console.print("  --fast         Hızlı mod (animasyon yok)")
            return
        else:
            i += 1
    
    run_simulation(size_gb=size_gb, seed=seed, fast=fast, num_devs=num_devs, daily_gb=daily_gb)


if __name__ == "__main__":
    main()
