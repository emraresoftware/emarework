"""
Hiyerarşik Adres Sistemi
========================

9 milyar düğümü benzersiz şekilde adresleme:

Adres formatı: "L{seviye}.{indeks0}.{indeks1}...{indeksN}"
- L0          → Kök lider
- L1.3        → Seviye 1, 4. takım lideri (0-indexed)
- L3.0.4.7    → Seviye 3, kök→dal0→dal4→dal7

Materialized Path: "0/3/7" → Hızlı alt ağaç sorguları için
"""

from __future__ import annotations
from typing import Optional
from src import HIERARCHY_DEPTH, BRANCH_FACTOR


class NodeAddress:
    """Bir düğümün hiyerarşideki adresini temsil eder."""
    
    def __init__(self, level: int, indices: list[int]):
        if level < 0 or level > HIERARCHY_DEPTH:
            raise ValueError(f"Seviye 0-{HIERARCHY_DEPTH} arasında olmalı, verilen: {level}")
        if len(indices) != level:
            raise ValueError(f"Seviye {level} için {level} indeks gerekli, verilen: {len(indices)}")
        for idx in indices:
            if idx < 0 or idx >= BRANCH_FACTOR:
                raise ValueError(f"İndeks 0-{BRANCH_FACTOR-1} arasında olmalı, verilen: {idx}")
        
        self.level = level
        self.indices = indices
    
    @classmethod
    def root(cls) -> NodeAddress:
        """Kök düğüm adresi"""
        return cls(level=0, indices=[])
    
    @classmethod
    def from_string(cls, address: str) -> NodeAddress:
        """'L3.0.4.7' formatından ayrıştır"""
        if address == "L0":
            return cls.root()
        
        parts = address.split(".")
        level = int(parts[0][1:])  # "L3" → 3
        indices = [int(p) for p in parts[1:]]
        return cls(level=level, indices=indices)
    
    def to_string(self) -> str:
        """Adres stringi: 'L3.0.4.7'"""
        if self.level == 0:
            return "L0"
        return f"L{self.level}." + ".".join(str(i) for i in self.indices)
    
    def to_path(self) -> str:
        """Materialized path: '0/4/7'"""
        if self.level == 0:
            return ""
        return "/".join(str(i) for i in self.indices)
    
    @property
    def parent(self) -> Optional[NodeAddress]:
        """Ebeveyn düğüm adresi"""
        if self.level == 0:
            return None
        return NodeAddress(level=self.level - 1, indices=self.indices[:-1])
    
    def child(self, index: int) -> NodeAddress:
        """Belirtilen indeksteki çocuk düğüm"""
        if self.level >= HIERARCHY_DEPTH:
            raise ValueError(f"Seviye {HIERARCHY_DEPTH} yaprak düğümdür, çocuğu olamaz")
        return NodeAddress(level=self.level + 1, indices=self.indices + [index])
    
    @property
    def children(self) -> list[NodeAddress]:
        """Tüm doğrudan çocuk düğümler"""
        if self.level >= HIERARCHY_DEPTH:
            return []
        return [self.child(i) for i in range(BRANCH_FACTOR)]
    
    @property
    def siblings(self) -> list[NodeAddress]:
        """Aynı ebeveynin diğer çocukları"""
        if self.level == 0:
            return []
        parent = self.parent
        return [parent.child(i) for i in range(BRANCH_FACTOR) if i != self.indices[-1]]
    
    def is_ancestor_of(self, other: NodeAddress) -> bool:
        """Bu düğüm, diğerinin atası mı?"""
        if self.level >= other.level:
            return False
        return other.indices[:self.level] == self.indices
    
    def is_descendant_of(self, other: NodeAddress) -> bool:
        """Bu düğüm, diğerinin torunu mu?"""
        return other.is_ancestor_of(self)
    
    @property
    def subtree_size(self) -> int:
        """Bu düğümün alt ağacındaki toplam düğüm sayısı (kendisi dahil)"""
        remaining_levels = HIERARCHY_DEPTH - self.level
        total = 0
        for i in range(remaining_levels + 1):
            total += BRANCH_FACTOR ** i
        return total
    
    @property
    def subtree_leaf_count(self) -> int:
        """Alt ağaçtaki yaprak düğüm sayısı"""
        remaining_levels = HIERARCHY_DEPTH - self.level
        return BRANCH_FACTOR ** remaining_levels
    
    def distance_to(self, other: NodeAddress) -> int:
        """İki düğüm arasındaki mesafe (en kısa yol)"""
        # Ortak atayı bul
        common_level = 0
        min_level = min(self.level, other.level)
        for i in range(min_level):
            if self.indices[i] == other.indices[i]:
                common_level = i + 1
            else:
                break
        
        return (self.level - common_level) + (other.level - common_level)
    
    def common_ancestor(self, other: NodeAddress) -> NodeAddress:
        """İki düğümün en yakın ortak atası"""
        common_indices = []
        min_level = min(self.level, other.level)
        for i in range(min_level):
            if self.indices[i] == other.indices[i]:
                common_indices.append(self.indices[i])
            else:
                break
        return NodeAddress(level=len(common_indices), indices=common_indices)
    
    def path_to(self, other: NodeAddress) -> list[NodeAddress]:
        """Bu düğümden diğerine giden yol"""
        ancestor = self.common_ancestor(other)
        
        # Yukarı çık
        path_up = []
        current = self
        while current.level > ancestor.level:
            path_up.append(current)
            current = current.parent
        
        # Aşağı in
        path_down = []
        current = other
        while current.level > ancestor.level:
            path_down.append(current)
            current = current.parent
        
        path_down.reverse()
        return path_up + [ancestor] + path_down
    
    def __repr__(self):
        return f"NodeAddress({self.to_string()})"
    
    def __eq__(self, other):
        if not isinstance(other, NodeAddress):
            return False
        return self.level == other.level and self.indices == other.indices
    
    def __hash__(self):
        return hash(self.to_string())


def format_node_count(count: int) -> str:
    """Büyük sayıları okunabilir formata çevir"""
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f} Milyar"
    elif count >= 1_000_000:
        return f"{count / 1_000_000:.1f} Milyon"
    elif count >= 1_000:
        return f"{count / 1_000:.1f} Bin"
    return str(count)


def level_node_count(level: int) -> int:
    """Belirli bir seviyedeki düğüm sayısı"""
    return BRANCH_FACTOR ** level


def level_summary() -> dict[int, dict]:
    """Tüm seviyelerin özeti"""
    summary = {}
    cumulative = 0
    for level in range(HIERARCHY_DEPTH + 1):
        count = level_node_count(level)
        cumulative += count
        summary[level] = {
            "level": level,
            "node_count": count,
            "node_count_str": format_node_count(count),
            "cumulative": cumulative,
            "cumulative_str": format_node_count(cumulative),
            "role": _level_role(level),
        }
    return summary


def _level_role(level: int) -> str:
    """Seviye bazlı varsayılan rol"""
    roles = {
        0: "Genel Koordinatör",
        1: "Bölge Direktörü",
        2: "Kıta Yöneticisi", 
        3: "Ülke Müdürü",
        4: "Bölge Müdürü",
        5: "Şehir Koordinatörü",
        6: "İlçe Lideri",
        7: "Takım Kaptanı",
        8: "Kıdemli Geliştirici",
        9: "Geliştirici",
        10: "Uygulayıcı",  # Yaprak düğüm - en alt seviye
    }
    return roles.get(level, f"Seviye-{level} Çalışan")
