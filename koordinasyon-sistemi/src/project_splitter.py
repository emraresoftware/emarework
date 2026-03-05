"""
Project Splitter - Yazılım projesini task'lara böl
İş yükünü AI worker'lara dağıtmak için projeyi analiz eder
"""
from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()


class TaskType(str, Enum):
    """Task tipleri"""
    ARCHITECTURE = "architecture"  # Mimari tasarım
    FRONTEND = "frontend"  # UI/UX geliştirme
    BACKEND = "backend"  # API/Server geliştirme
    DATABASE = "database"  # Veritabanı tasarım/migration
    AI_ML = "ai_ml"  # AI/ML entegrasyonu
    DEVOPS = "devops"  # Deployment/CI-CD
    TESTING = "testing"  # Test yazımı
    DOCUMENTATION = "documentation"  # Dokümantasyon
    SECURITY = "security"  # Güvenlik analizi
    INTEGRATION = "integration"  # 3rd party entegrasyonlar


class ProjectTask(BaseModel):
    """Bir proje task'ı"""
    id: str
    title: str
    description: str
    type: TaskType
    requirements: List[str]  # Gerekli expertise'ler
    estimated_hours: float
    dependencies: List[str] = []  # Diğer task ID'leri
    priority: int = 5  # 1-10
    deliverables: List[str] = []  # Beklenen çıktılar


class SoftwareProject(BaseModel):
    """Yazılım projesi tanımı"""
    name: str
    description: str
    tech_stack: List[str]
    requirements: List[str]
    estimated_total_hours: Optional[float] = None


class ProjectSplitter:
    """Projeyi task'lara böl"""
    
    @staticmethod
    def analyze_project(project: SoftwareProject) -> Dict:
        """
        Projeyi analiz et ve gerekli task'ları belirle
        
        Returns:
            {
                "total_tasks": int,
                "estimated_hours": float,
                "tasks": List[ProjectTask],
                "dependency_graph": Dict
            }
        """
        tasks = []
        
        # 1. Mimari Tasarım (Her zaman ilk)
        tasks.append(ProjectTask(
            id="task_architecture",
            title="Sistem Mimarisi Tasarımı",
            description=f"{project.name} için sistem mimarisi ve component tasarımı",
            type=TaskType.ARCHITECTURE,
            requirements=["backend", "database", "infrastructure"],
            estimated_hours=8,
            priority=10,
            deliverables=[
                "Sistem mimarisi diyagramı",
                "Component diagram",
                "API specification"
            ]
        ))
        
        # 2. Veritabanı Tasarımı
        if any(db in " ".join(project.tech_stack).lower() for db in ["sql", "database", "postgres", "mysql", "mongo"]):
            tasks.append(ProjectTask(
                id="task_database",
                title="Veritabanı Tasarımı",
                description="Database schema, migrations, ve indexes",
                type=TaskType.DATABASE,
                requirements=["database", "backend"],
                estimated_hours=6,
                dependencies=["task_architecture"],
                priority=9,
                deliverables=[
                    "ERD diagram",
                    "Migration scripts",
                    "Seed data"
                ]
            ))
        
        # 3. Backend API Geliştirme
        if any(tech in " ".join(project.tech_stack).lower() for tech in ["fastapi", "flask", "laravel", "express", "django"]):
            tasks.append(ProjectTask(
                id="task_backend_core",
                title="Core Backend API",
                description="REST API endpoints, authentication, business logic",
                type=TaskType.BACKEND,
                requirements=["backend", "python" if "python" in " ".join(project.tech_stack).lower() else "php"],
                estimated_hours=20,
                dependencies=["task_architecture", "task_database"] if "task_database" in [t.id for t in tasks] else ["task_architecture"],
                priority=9,
                deliverables=[
                    "API endpoints",
                    "Authentication system",
                    "Core business logic"
                ]
            ))
        
        # 4. Frontend UI Geliştirme
        if any(tech in " ".join(project.tech_stack).lower() for tech in ["react", "vue", "next.js", "tailwind"]):
            tasks.append(ProjectTask(
                id="task_frontend_ui",
                title="Frontend UI Geliştirme",
                description="Kullanıcı arayüzü, component'ler, state management",
                type=TaskType.FRONTEND,
                requirements=["frontend", "react" if "react" in " ".join(project.tech_stack).lower() else "vue"],
                estimated_hours=16,
                dependencies=["task_backend_core"] if "task_backend_core" in [t.id for t in tasks] else ["task_architecture"],
                priority=8,
                deliverables=[
                    "UI components",
                    "Pages/Views",
                    "State management"
                ]
            ))
        
        # 5. AI/ML Entegrasyonu
        if any(ai in " ".join(project.tech_stack + project.requirements).lower() for ai in ["ai", "gemini", "openai", "ml", "llm"]):
            tasks.append(ProjectTask(
                id="task_ai_integration",
                title="AI/ML Entegrasyonu",
                description="AI model entegrasyonu, prompt engineering, context management",
                type=TaskType.AI_ML,
                requirements=["ai", "python", "backend"],
                estimated_hours=12,
                dependencies=["task_backend_core"] if "task_backend_core" in [t.id for t in tasks] else [],
                priority=7,
                deliverables=[
                    "AI service integration",
                    "Prompt templates",
                    "Context caching"
                ]
            ))
        
        # 6. DevOps & Deployment
        tasks.append(ProjectTask(
            id="task_devops",
            title="DevOps & Deployment",
            description="Docker, CI/CD, server setup",
            type=TaskType.DEVOPS,
            requirements=["devops", "docker"],
            estimated_hours=8,
            dependencies=[t.id for t in tasks if t.type in [TaskType.BACKEND, TaskType.FRONTEND]],
            priority=6,
            deliverables=[
                "Dockerfile",
                "docker-compose.yml",
                "CI/CD pipeline",
                "Deployment docs"
            ]
        ))
        
        # 7. Testing
        tasks.append(ProjectTask(
            id="task_testing",
            title="Test Suite",
            description="Unit tests, integration tests, E2E tests",
            type=TaskType.TESTING,
            requirements=["backend", "testing"],
            estimated_hours=10,
            dependencies=[t.id for t in tasks if t.type in [TaskType.BACKEND, TaskType.FRONTEND]],
            priority=7,
            deliverables=[
                "Unit tests",
                "Integration tests",
                "Test coverage report"
            ]
        ))
        
        # 8. Security
        if "security" in " ".join(project.requirements).lower():
            tasks.append(ProjectTask(
                id="task_security",
                title="Security Implementation",
                description="Security audit, pentest, fixes",
                type=TaskType.SECURITY,
                requirements=["security", "backend"],
                estimated_hours=8,
                dependencies=[t.id for t in tasks if t.type == TaskType.BACKEND],
                priority=9,
                deliverables=[
                    "Security audit report",
                    "Vulnerability fixes",
                    "Security best practices"
                ]
            ))
        
        # 9. Documentation
        tasks.append(ProjectTask(
            id="task_documentation",
            title="Dokümantasyon",
            description="API docs, user guide, deployment guide",
            type=TaskType.DOCUMENTATION,
            requirements=["documentation"],
            estimated_hours=6,
            dependencies=[],  # Paralel çalışabilir
            priority=5,
            deliverables=[
                "API documentation",
                "User guide",
                "Deployment guide",
                "README.md"
            ]
        ))
        
        total_hours = sum(t.estimated_hours for t in tasks)
        
        return {
            "total_tasks": len(tasks),
            "estimated_hours": total_hours,
            "tasks": tasks,
            "dependency_graph": ProjectSplitter._build_dependency_graph(tasks),
            "parallel_possible": ProjectSplitter._calculate_parallel_potential(tasks)
        }
    
    @staticmethod
    def _build_dependency_graph(tasks: List[ProjectTask]) -> Dict[str, List[str]]:
        """Task bağımlılık grafiği oluştur"""
        graph = {}
        for task in tasks:
            graph[task.id] = task.dependencies
        return graph
    
    @staticmethod
    def _calculate_parallel_potential(tasks: List[ProjectTask]) -> Dict:
        """Paralel çalıştırılabilir task'ları hesapla"""
        # Bağımlılığı olmayan task'lar paralel çalışabilir
        independent = [t for t in tasks if not t.dependencies]
        
        return {
            "max_parallel_workers": len(independent),
            "estimated_time_saved": sum(t.estimated_hours for t in independent) * 0.7,  # %30 overhead
            "parallelizable_tasks": [t.id for t in independent]
        }


if __name__ == "__main__":
    # Test
    sample_project = SoftwareProject(
        name="E-Ticaret Platformu",
        description="Multi-tenant SaaS e-ticaret platformu",
        tech_stack=["FastAPI", "React 19", "PostgreSQL", "Redis", "Gemini AI"],
        requirements=[
            "RESTful API",
            "Admin panel",
            "AI chatbot",
            "Payment integration",
            "Multi-tenant architecture"
        ]
    )
    
    splitter = ProjectSplitter()
    result = splitter.analyze_project(sample_project)
    
    print(f"\n📦 Proje: {sample_project.name}")
    print(f"{'='*60}")
    print(f"Toplam Task: {result['total_tasks']}")
    print(f"Tahmini Süre: {result['estimated_hours']} saat")
    print(f"Paralel Potansiyel: {result['parallel_possible']['max_parallel_workers']} worker")
    
    print(f"\n📋 Task Listesi:")
    for task in result['tasks']:
        deps = f" (Bağımlılık: {len(task.dependencies)})" if task.dependencies else " (Bağımsız)"
        print(f"\n  {task.type.value.upper()}{deps}")
        print(f"  → {task.title}")
        print(f"    Süre: {task.estimated_hours}h | Öncelik: {task.priority}/10")
        print(f"    Gerekli: {', '.join(task.requirements)}")
