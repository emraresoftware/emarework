"""
HIVE COORDINATOR - 9 Milyar Düğümlü Hiyerarşik Koordinasyon Sistemi
====================================================================

Mimari:
    Seviye 0: Lider (1 kişi)
    Seviye 1: 10 Takım Lideri
    Seviye 2: 100 Alt Takım Lideri
    ...
    Seviye 9: 1,000,000,000 Uç Düğüm
    Toplam: ~9,999,999,999 düğüm ≈ 10 milyar

Her düğüm tam olarak 10 alt düğüme sahip (yaprak düğümler hariç).
Görevler yukarıdan aşağı akar, durum raporları aşağıdan yukarı toplanır.
"""

from .config import settings

__version__ = settings.version
HIERARCHY_DEPTH = settings.hierarchy_depth
BRANCH_FACTOR = settings.branch_factor
TOTAL_NODES = sum(BRANCH_FACTOR**i for i in range(HIERARCHY_DEPTH + 1))

__all__ = ["settings", "__version__", "HIERARCHY_DEPTH", "BRANCH_FACTOR", "TOTAL_NODES"]
