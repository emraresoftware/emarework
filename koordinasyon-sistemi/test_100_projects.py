#!/usr/bin/env python3
"""
100 Proje Test Senaryosu - EmareUlak Entegrasyonu
=================================================

EmareUlak için 100 projelik test dağıtımı yapar.
Hiyerarşiyi otomatik kurar, projeleri dağıtır ve izler.

Kullanım:
    python test_100_projects.py                    # Varsayılan test
    python test_100_projects.py --projects 50      # 50 proje
    python test_100_projects.py --strategy cascade # Cascade stratejisi
    python test_100_projects.py --parallel         # Paralel dağıtım
    python test_100_projects.py --api http://...   # Özel API URL
"""

import asyncio
import argparse
import random
import time
from datetime import datetime
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import box
import httpx

console = Console()


class EmareUlakTestRunner:
    """100 Proje test çalıştırıcı"""
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        project_count: int = 100,
        strategy: str = "weighted",
        parallel: bool = True,
    ):
        self.api_url = api_url
        self.project_count = project_count
        self.strategy = strategy
        self.parallel = parallel
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def setup_hierarchy(self) -> Dict[str, Any]:
        """Hiyerarşiyi kur (L0 → L1(10) → L2(100))"""
        console.print("\n[bold cyan]📊 Hiyerarşi kuruluyor...[/bold cyan]")
        
        try:
            response = await self.client.post(
                f"{self.api_url}/batch/register-tree",
                params={"root_address": "L0", "depth": 2},
            )
            response.raise_for_status()
            result = response.json()
            
            console.print(f"[green]✓[/green] {result['registered_nodes']} düğüm kaydedildi")
            console.print(f"[green]✓[/green] Toplam sistem düğümü: {result['total_nodes_in_system']}")
            
            return result
        except Exception as e:
            console.print(f"[red]✗ Hiyerarşi kurulumu hatası: {e}[/red]")
            raise
    
    def generate_projects(self) -> List[Dict[str, Any]]:
        """Test projeleri üret"""
        console.print(f"\n[bold cyan]📦 {self.project_count} test projesi üretiliyor...[/bold cyan]")
        
        priorities = ["low", "medium", "high", "critical"]
        priority_weights = [0.3, 0.4, 0.2, 0.1]
        
        project_templates = [
            "Web Uygulaması Geliştirme",
            "Mobil App Backend",
            "API Entegrasyonu",
            "Database Migration",
            "Frontend Refactoring",
            "Microservice Dönüşümü",
            "CI/CD Pipeline Kurulumu",
            "Test Otomasyonu",
            "Güvenlik Güncellemeleri",
            "Performans Optimizasyonu",
            "Dökümantasyon",
            "Code Review Sistemi",
            "Monitoring Dashboard",
            "Log Analiz Sistemi",
            "Kullanıcı Yönetimi",
            "Payment Gateway",
            "Email Servisi",
            "SMS Entegrasyonu",
            "File Storage Sistemi",
            "Cache Sistemi",
        ]
        
        projects = []
        for i in range(self.project_count):
            template = random.choice(project_templates)
            priority = random.choices(priorities, weights=priority_weights)[0]
            estimated_kb = random.randint(10240, 102400)  # 10-100 MB
            
            project = {
                "project_id": f"ULAK-{i+1:03d}",
                "title": f"{template} #{i+1}",
                "description": f"EmareUlak test projesi - {template}",
                "priority": priority,
                "estimated_kb": estimated_kb,
                "tags": [f"batch-{self.project_count}", "test", priority],
            }
            projects.append(project)
        
        console.print(f"[green]✓[/green] {len(projects)} proje hazırlandı")
        return projects
    
    async def distribute_projects(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Projeleri dağıt"""
        console.print(f"\n[bold cyan]🚀 Projeler dağıtılıyor...[/bold cyan]")
        console.print(f"[dim]Strateji: {self.strategy}, Paralel: {self.parallel}[/dim]")
        
        start_time = time.time()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Dağıtım yapılıyor ({self.strategy})...",
                    total=self.project_count,
                )
                
                response = await self.client.post(
                    f"{self.api_url}/emareulak/batch",
                    json={
                        "projects": projects,
                        "parallel": self.parallel,
                        "strategy": self.strategy,
                    },
                )
                response.raise_for_status()
                result = response.json()
                
                progress.update(task, completed=self.project_count)
            
            elapsed = time.time() - start_time
            
            console.print(f"\n[green]✓[/green] Dağıtım tamamlandı ({elapsed:.2f}s)")
            console.print(f"  • Başarılı: [green]{result['success']}[/green]")
            console.print(f"  • Hatalı: [red]{result['errors']}[/red]")
            console.print(f"  • Ortalama: [yellow]{elapsed/self.project_count*1000:.1f}ms/proje[/yellow]")
            
            return result
        except Exception as e:
            console.print(f"[red]✗ Dağıtım hatası: {e}[/red]")
            raise
    
    async def show_distribution_table(self, result: Dict[str, Any]):
        """Dağıtım sonuçlarını tablo olarak göster"""
        console.print("\n[bold cyan]📋 Dağıtım Detayları:[/bold cyan]")
        
        table = Table(box=box.ROUNDED, show_lines=False)
        table.add_column("Proje ID", style="cyan")
        table.add_column("Task ID", style="yellow")
        table.add_column("Atandı", style="green")
        table.add_column("Durum", style="bold")
        
        # İlk 20 projeyi göster
        for r in result['results'][:20]:
            status_style = "green" if r['status'] == "success" else "red"
            table.add_row(
                r['project_id'],
                r['task_uid'][:12] + "..." if r['task_uid'] else "-",
                r['assigned_to'],
                f"[{status_style}]{r['status']}[/{status_style}]",
            )
        
        if len(result['results']) > 20:
            table.add_row(
                "...",
                "...",
                "...",
                f"[dim]+{len(result['results']) - 20} proje daha[/dim]",
            )
        
        console.print(table)
    
    async def check_system_status(self):
        """Sistem durumunu kontrol et"""
        console.print("\n[bold cyan]🔍 Sistem durumu kontrol ediliyor...[/bold cyan]")
        
        try:
            # Genel durum
            response = await self.client.get(f"{self.api_url}/")
            response.raise_for_status()
            overview = response.json()
            
            # EmareUlak stats
            response = await self.client.get(f"{self.api_url}/emareulak/stats")
            response.raise_for_status()
            ulak_stats = response.json()
            
            # Göster
            table = Table(title="Sistem Durumu", box=box.DOUBLE_EDGE)
            table.add_column("Metrik", style="bold cyan")
            table.add_column("Değer", style="yellow")
            
            system_overview = overview.get('overview', {})
            table.add_row("Toplam Düğüm", str(system_overview.get('total_registered_nodes', 0)))
            table.add_row("Aktif Düğüm", str(system_overview.get('active_nodes', 0)))
            table.add_row("EmareUlak Projeler", str(ulak_stats.get('total_projects', 0)))
            table.add_row("Dağıtım Stratejisi", ulak_stats.get('strategy', '-'))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]✗ Durum kontrolü hatası: {e}[/red]")
    
    async def run(self):
        """Ana test senaryosu"""
        console.print(Panel.fit(
            f"[bold cyan]EmareUlak 100 Proje Test Senaryosu[/bold cyan]\n\n"
            f"API: {self.api_url}\n"
            f"Proje Sayısı: {self.project_count}\n"
            f"Strateji: {self.strategy}\n"
            f"Paralel: {'Evet' if self.parallel else 'Hayır'}\n"
            f"Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            title="🚀 Test Başlıyor",
            border_style="cyan",
        ))
        
        try:
            # 1. Hiyerarşiyi kur
            await self.setup_hierarchy()
            await asyncio.sleep(0.5)
            
            # 2. Projeleri üret
            projects = self.generate_projects()
            await asyncio.sleep(0.5)
            
            # 3. Dağıt
            result = await self.distribute_projects(projects)
            await asyncio.sleep(0.5)
            
            # 4. Sonuçları göster
            await self.show_distribution_table(result)
            await asyncio.sleep(0.5)
            
            # 5. Sistem durumu
            await self.check_system_status()
            
            console.print("\n[bold green]✓ Test başarıyla tamamlandı![/bold green]")
            
        except Exception as e:
            console.print(f"\n[bold red]✗ Test hatası: {e}[/bold red]")
            raise
        finally:
            await self.client.aclose()


async def main():
    parser = argparse.ArgumentParser(description="EmareUlak 100 Proje Test")
    parser.add_argument("--api", default="http://localhost:8000", help="API URL")
    parser.add_argument("--projects", type=int, default=100, help="Proje sayısı")
    parser.add_argument("--strategy", default="weighted", 
                       choices=["weighted", "cascade", "round-robin", "least-loaded"],
                       help="Dağıtım stratejisi")
    parser.add_argument("--parallel", action="store_true", default=True,
                       help="Paralel dağıtım")
    parser.add_argument("--sequential", action="store_true",
                       help="Sıralı dağıtım (parallel=False)")
    
    args = parser.parse_args()
    
    runner = EmareUlakTestRunner(
        api_url=args.api,
        project_count=args.projects,
        strategy=args.strategy,
        parallel=not args.sequential,
    )
    
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
