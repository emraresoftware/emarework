"""
YILLIK PROJE SİMÜLASYONU
=========================

Yazılım projesini 9 milyar kişilik hiyerarşiye dağıtıp
1 yıl (365 gün) boyunca haftalık sprintlerle simüle eder.

HESAP:
    Varsayılan proje:  365,000 GB (~356 TB)
    Simülasyon düğüm:  1,111 düğüm (L0-L3, 3 seviye)
    Yaprak (L3):       1,000 geliştirici
    Kişi başı hedef:   ~1 GB/gün
    Sprint süresi:     7 gün (52 sprint/yıl)
    Sprint hedefi:     ~7 GB/kişi/sprint

Her geliştirici herbir gün:
    - Yeni kod yazar (ortalama ~287 KB, ±%40 varyans)
    - Bug yaratma olasılığı (%5-15, seviyeye göre)
    - Code review yapar (eşler arası)
    - Refactoring yapar (%2 olasılık, mevcut kodun %5-20'si)
    - Hastalanabilir / tatile çıkabilir (%3 olasılık)
    
HER GÜN BİTİMİNDE:
    - Aşağıdan yukarı rapor toplanır
    - Yük dengeleme yapılır
    - Sprint sonu ise sprint raporu oluşturulur
    
VERİ BOYUTU: < 5 MB RAM (sadece sayaçlar + durum)
"""

from __future__ import annotations
import random
import math
import hashlib
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict

# ─── Sabitler ────────────────────────────────────────────────────────────────

TOTAL_CODE_KB = 100 * 1024 * 1024    # 100 GB
SIMULATION_DAYS = 365
SPRINT_DAYS = 7
BRANCH_FACTOR = 10
TOTAL_DEVELOPERS = 100               # 100 geliştirici
HIERARCHY_DEPTH = 2                   # L0 → L1(10) → L2(100 dev)
DAILY_TARGET_KB = 1 * 1024 * 1024     # 1 GB/kişi/gün

# Geliştirici yetenek dağılımı
SKILL_LEVELS = {
    "junior":     {"ratio": 0.30, "speed_mult": 0.6,  "bug_rate": 0.15, "review_quality": 0.7},
    "mid":        {"ratio": 0.35, "speed_mult": 1.0,  "bug_rate": 0.08, "review_quality": 0.85},
    "senior":     {"ratio": 0.25, "speed_mult": 1.4,  "bug_rate": 0.04, "review_quality": 0.95},
    "principal":  {"ratio": 0.10, "speed_mult": 1.8,  "bug_rate": 0.02, "review_quality": 0.98},
}

# Olay olasılıkları
EVENT_RATES = {
    "sick_day": 0.02,           # Hasta (%2/gün)
    "vacation": 0.01,           # Tatil (%1/gün, ort. 3-7 gün)
    "refactor": 0.03,           # Refactoring tetikleme (%3/gün)
    "critical_bug": 0.005,      # Kritik bug (%0.5/gün)
    "team_meeting": 0.15,       # Toplantı (%15/gün, verimlilik düşer)
    "breakthrough": 0.01,       # Verimlilik patlaması (%1/gün)
    "burnout": 0.003,           # Tükenmişlik (%0.3/gün)
    "dependency_block": 0.02,   # Bağımlılık sorunu (%2/gün)
}


# ─── Veri Yapıları ───────────────────────────────────────────────────────────

class DevStatus(str, Enum):
    ACTIVE = "active"
    SICK = "sick"
    VACATION = "vacation"
    BURNOUT = "burnout"
    BLOCKED = "blocked"


@dataclass
class DayEvent:
    """Bir günde gerçekleşen olay"""
    day: int
    event_type: str
    node_address: str
    detail: str
    impact_kb: float = 0.0


@dataclass  
class Developer:
    """L3 yaprak düğüm - gerçek kod yazan geliştirici"""
    address: str
    skill: str  # junior, mid, senior, principal
    
    # Durum
    status: DevStatus = DevStatus.ACTIVE
    status_days_remaining: int = 0
    
    # Üretim metrikleri
    total_code_produced_kb: float = 0.0
    total_bugs_created: int = 0
    total_bugs_fixed: int = 0
    total_reviews_done: int = 0
    total_refactored_kb: float = 0.0
    
    # Günlük
    today_code_kb: float = 0.0
    
    # Performans
    morale: float = 1.0       # 0.3 - 1.5 arası
    fatigue: float = 0.0      # 0.0 - 1.0 arası (1.0 = burnout)
    streak_days: int = 0      # Kesintisiz çalışma günü
    
    # Hedef
    assigned_target_kb: float = 0.0
    
    @property
    def speed_mult(self) -> float:
        base = SKILL_LEVELS[self.skill]["speed_mult"]
        morale_factor = self.morale
        fatigue_factor = max(0.3, 1.0 - self.fatigue * 0.5)
        return base * morale_factor * fatigue_factor
    
    @property
    def bug_rate(self) -> float:
        base = SKILL_LEVELS[self.skill]["bug_rate"]
        fatigue_factor = 1.0 + self.fatigue * 0.5
        return min(0.3, base * fatigue_factor)
    
    @property
    def is_available(self) -> bool:
        return self.status == DevStatus.ACTIVE


@dataclass
class TeamNode:
    """L0-L2 yönetici düğüm"""
    address: str
    level: int
    children: list[str] = field(default_factory=list)
    
    # Toplu metrikler
    total_code_kb: float = 0.0
    total_bugs: int = 0
    total_bugs_fixed: int = 0
    active_devs: int = 0
    total_devs: int = 0
    avg_morale: float = 1.0
    sprint_velocity_kb: float = 0.0
    
    # Hedef
    assigned_target_kb: float = 0.0
    
    # Mesajlar
    messages_sent: int = 0
    messages_received: int = 0
    escalations_received: int = 0


@dataclass
class SprintReport:
    """Haftalık sprint raporu"""
    sprint_number: int
    start_day: int
    end_day: int
    
    code_produced_kb: float = 0.0
    code_target_kb: float = 0.0
    bugs_created: int = 0
    bugs_fixed: int = 0
    reviews_done: int = 0
    refactored_kb: float = 0.0
    
    active_developers: int = 0
    sick_days: int = 0
    vacation_days: int = 0
    blocked_days: int = 0
    burnout_cases: int = 0
    
    critical_events: list[str] = field(default_factory=list)
    
    # Verimlilik
    velocity_kb_per_dev: float = 0.0
    plan_completion_pct: float = 0.0
    cumulative_progress_pct: float = 0.0
    
    # Mesajlaşma
    total_messages: int = 0
    escalations: int = 0


@dataclass
class DailySnapshot:
    """Günlük durum fotoğrafı (hafif - sadece sayılar)"""
    day: int
    date: date = None
    
    code_produced_today_kb: float = 0.0
    cumulative_code_kb: float = 0.0
    progress_pct: float = 0.0
    
    active_devs: int = 0
    sick_devs: int = 0
    vacation_devs: int = 0
    blocked_devs: int = 0
    burnout_devs: int = 0
    
    bugs_today: int = 0
    cumulative_bugs: int = 0
    bugs_fixed_today: int = 0
    cumulative_bugs_fixed: int = 0
    
    avg_morale: float = 1.0
    avg_fatigue: float = 0.0
    
    messages_today: int = 0
    escalations_today: int = 0
    
    events_today: int = 0


# ─── Ana Simülasyon Motoru ───────────────────────────────────────────────────

class YearSimulation:
    """
    1 yıllık proje simülasyonu.
    
    100GB kod projesini 1000 geliştiriciye dağıtır ve 365 gün boyunca
    günlük bazda simüle eder. Her gün:
    
    1. Geliştirici durumları güncellenir (hasta, tatil, vb.)
    2. Random olaylar tetiklenir
    3. Kod üretimi gerçekleşir
    4. Bug'lar oluşur ve düzeltilir
    5. Code review yapılır
    6. Raporlar yukarı toplanır
    7. Yük dengeleme yapılır
    8. Sprint sonu ise sprint raporu oluşturulur
    """
    
    def __init__(self, 
                 total_code_kb: float = TOTAL_CODE_KB,
                 num_developers: int = TOTAL_DEVELOPERS,
                 daily_per_dev_kb: float = DAILY_TARGET_KB,
                 seed: int = 42,
                 start_date: date = date(2026, 3, 2)):
        
        self.total_target_kb = total_code_kb
        self.num_developers = num_developers
        self.branch_factor = BRANCH_FACTOR
        self.start_date = start_date
        self.rng = random.Random(seed)
        
        # Hiyerarşi derinliğini geliştirici sayısından hesapla
        # 10 dev → depth=1, 100 dev → depth=2, 1000 dev → depth=3
        self.hierarchy_depth = max(1, int(math.log(num_developers, self.branch_factor)))
        
        # Düğümler
        self.developers: dict[str, Developer] = {}
        self.teams: dict[str, TeamNode] = {}
        
        # Zaman serisi verileri
        self.daily_snapshots: list[DailySnapshot] = []
        self.sprint_reports: list[SprintReport] = []
        self.all_events: list[DayEvent] = []
        
        # Sprint izleme
        self.current_sprint: int = 0
        self.sprint_start_day: int = 0
        
        # Kümülatif
        self.cumulative_code_kb: float = 0.0
        self.cumulative_bugs: int = 0
        self.cumulative_bugs_fixed: int = 0
        self.cumulative_messages: int = 0
        
        # Kişi başı günlük hedef
        self.daily_target_kb = daily_per_dev_kb
        
        # Başlat
        self._init_hierarchy()
        self._distribute_targets()
    
    def _init_hierarchy(self):
        """Hiyerarşiyi dinamik oluştur.
        
        depth=2, branch=10 → L0(1) → L1(10 lead) → L2(100 dev)
        depth=3, branch=10 → L0(1) → L1(10) → L2(100 lead) → L3(1000 dev)
        """
        bf = self.branch_factor
        depth = self.hierarchy_depth
        dev_level = depth  # Geliştiricilerin olduğu seviye
        
        # Yönetim katmanlarını oluştur (L0 ... L{depth-1})
        # L0 - Kök
        self.teams["L0"] = TeamNode(
            address="L0", level=0,
            children=[f"L1.{i}" for i in range(bf)],
        )
        
        # Ara yönetim katmanları (L1 ... L{depth-1})
        for level in range(1, depth):
            # Bu seviyedeki tüm düğümleri oluştur
            count_at_level = bf ** level
            for flat_idx in range(count_at_level):
                # Adres hesapla: L{level}.i.j.k...
                parts = []
                tmp = flat_idx
                for _ in range(level):
                    parts.append(tmp % bf)
                    tmp //= bf
                parts.reverse()
                addr = f"L{level}." + ".".join(str(p) for p in parts)
                
                # Çocuk adresleri
                if level < depth - 1:
                    # Sonraki yönetim katmanı
                    children = [f"L{level+1}." + ".".join(str(p) for p in parts) + f".{k}" for k in range(bf)]
                else:
                    # Yaprak geliştiriciler
                    children = [f"L{dev_level}." + ".".join(str(p) for p in parts) + f".{k}" for k in range(bf)]
                
                self.teams[addr] = TeamNode(
                    address=addr, level=level,
                    children=children,
                )
        
        # Geliştiricileri yerleştir (L{depth} yaprak düğümler)
        skills = []
        for skill, info in SKILL_LEVELS.items():
            count = int(self.num_developers * info["ratio"])
            skills.extend([skill] * count)
        while len(skills) < self.num_developers:
            skills.append("mid")
        self.rng.shuffle(skills)
        
        dev_idx = 0
        total_devs = bf ** depth
        for flat_idx in range(total_devs):
            parts = []
            tmp = flat_idx
            for _ in range(depth):
                parts.append(tmp % bf)
                tmp //= bf
            parts.reverse()
            addr = f"L{dev_level}." + ".".join(str(p) for p in parts)
            self.developers[addr] = Developer(
                address=addr,
                skill=skills[dev_idx],
                morale=round(self.rng.uniform(0.8, 1.2), 2),
            )
            dev_idx += 1
        
        # Takım düğümlerinin geliştirici sayısını set et
        for team in self.teams.values():
            levels_below = depth - team.level
            team.total_devs = bf ** levels_below
    
    def _distribute_targets(self):
        """Kod hedeflerini eşit dağıt"""
        per_dev = self.total_target_kb / self.num_developers
        for dev in self.developers.values():
            dev.assigned_target_kb = per_dev
        
        # Takım hedeflerini hesapla
        for team in self.teams.values():
            team.assigned_target_kb = per_dev * team.total_devs
    
    # ═════════════════════════════════════════════════════════════════════
    # ANA SİMÜLASYON DÖNGÜSÜ
    # ═════════════════════════════════════════════════════════════════════
    
    def run(self, progress_callback=None) -> dict:
        """
        365 günlük simülasyonu çalıştır.
        
        Returns: Yıl sonu özet raporu
        """
        for day in range(1, SIMULATION_DAYS + 1):
            current_date = self.start_date + timedelta(days=day - 1)
            is_weekend = current_date.weekday() >= 5
            
            # Sprint kontrolü
            if (day - 1) % SPRINT_DAYS == 0:
                if self.current_sprint > 0:
                    self._finalize_sprint(day - 1)
                self.current_sprint += 1
                self.sprint_start_day = day
            
            # Günlük simülasyon
            snapshot = self._simulate_day(day, current_date, is_weekend)
            self.daily_snapshots.append(snapshot)
            
            if progress_callback:
                progress_callback(day, snapshot)
        
        # Son sprinti kapat
        self._finalize_sprint(SIMULATION_DAYS)
        
        return self._generate_final_report()
    
    def _simulate_day(self, day: int, current_date: date, is_weekend: bool) -> DailySnapshot:
        """Tek bir günü simüle et"""
        
        snapshot = DailySnapshot(day=day, date=current_date)
        day_events = []
        day_messages = 0
        day_escalations = 0
        
        # ─── 1. DURUM GÜNCELLEMELERİ ───────────────────────────────────
        for dev in self.developers.values():
            # Mevcut durum süreleri
            if dev.status != DevStatus.ACTIVE and dev.status_days_remaining > 0:
                dev.status_days_remaining -= 1
                if dev.status_days_remaining <= 0:
                    old_status = dev.status
                    dev.status = DevStatus.ACTIVE
                    day_events.append(DayEvent(
                        day=day, event_type="status_change",
                        node_address=dev.address,
                        detail=f"{old_status.value} → active",
                    ))
            
            # Yeni olaylar (sadece aktif geliştiriciler için)
            if dev.is_available and not is_weekend:
                self._process_random_events(dev, day, day_events)
        
        # ─── 2. KOD ÜRETİMİ ─────────────────────────────────────────────
        for dev in self.developers.values():
            dev.today_code_kb = 0.0
            
            if not dev.is_available or is_weekend:
                continue
            
            # Toplantı günü ise verimlilik düşer
            meeting_penalty = 1.0
            if self.rng.random() < EVENT_RATES["team_meeting"]:
                meeting_penalty = 0.6
                day_messages += 3  # Toplantı mesajları
            
            # Günlük kod üretimi
            base_output = self.daily_target_kb
            variance = self.rng.gauss(1.0, 0.25)  # ±%25 varyans
            variance = max(0.3, min(2.0, variance))
            
            daily_kb = base_output * dev.speed_mult * variance * meeting_penalty
            daily_kb = max(0, daily_kb)
            
            dev.today_code_kb = daily_kb
            dev.total_code_produced_kb += daily_kb
            snapshot.code_produced_today_kb += daily_kb
            
            # Yorgunluk artışı
            dev.fatigue = min(1.0, dev.fatigue + 0.008)
            dev.streak_days += 1
            
            # Hafta sonu dinlenme (Cuma kontrolü)
            if current_date.weekday() == 4:
                dev.fatigue = max(0, dev.fatigue - 0.04)
        
        # ─── 3. BUG OLUŞTURMA ───────────────────────────────────────────
        for dev in self.developers.values():
            if dev.today_code_kb <= 0:
                continue
            
            # Her 100 KB kod için bug olasılığı (binomial yaklaşımı)
            chunks = max(1, int(dev.today_code_kb / 100))
            # Binomial: n * p yerine normal yaklaşım kullan (hızlı)
            expected = chunks * dev.bug_rate
            if expected > 5:
                # Normal yaklaşım: N(np, sqrt(np(1-p)))
                std = math.sqrt(expected * (1 - dev.bug_rate))
                bugs = max(0, int(self.rng.gauss(expected, std) + 0.5))
            else:
                # Küçük sayılar için doğrudan
                bugs = sum(1 for _ in range(min(chunks, 50)) if self.rng.random() < dev.bug_rate)
            
            if bugs > 0:
                dev.total_bugs_created += bugs
                snapshot.bugs_today += bugs
                self.cumulative_bugs += bugs
                
                # Kritik bug eskalasyonu
                if bugs >= 3 or self.rng.random() < EVENT_RATES["critical_bug"]:
                    day_escalations += 1
                    day_messages += 5  # Eskalasyon mesaj zinciri
                    day_events.append(DayEvent(
                        day=day, event_type="critical_bug",
                        node_address=dev.address,
                        detail=f"Kritik bug! {bugs} bug oluştu",
                        impact_kb=-dev.today_code_kb * 0.2,  # %20 geri alma
                    ))
        
        # ─── 4. BUG DÜZELTME (eşler arası code review) ──────────────────
        available_devs = [d for d in self.developers.values() if d.is_available]
        
        # Her takımda (yaprak öncesi seviye) eşler arası review
        parent_level = self.hierarchy_depth - 1
        for team_addr, team in self.teams.items():
            if team.level != parent_level:
                continue
            
            team_devs = [
                self.developers[child_addr]
                for child_addr in team.children
                if child_addr in self.developers and self.developers[child_addr].is_available
            ]
            
            if len(team_devs) < 2:
                continue
            
            # Takım içi review pairs
            reviewers = self.rng.sample(team_devs, min(len(team_devs), 4))
            for reviewer in reviewers:
                # Review kalitesine göre bug bul
                review_quality = SKILL_LEVELS[reviewer.skill]["review_quality"]
                if self.rng.random() < review_quality * 0.3:  # %30 × kalite
                    # Bug düzelt
                    if self.cumulative_bugs > self.cumulative_bugs_fixed:
                        reviewer.total_bugs_fixed += 1
                        reviewer.total_reviews_done += 1
                        snapshot.bugs_fixed_today += 1
                        self.cumulative_bugs_fixed += 1
                        day_messages += 2  # Review mesajları
        
        # ─── 5. REFACTORING ─────────────────────────────────────────────
        for dev in self.developers.values():
            if not dev.is_available or is_weekend:
                continue
            if self.rng.random() < EVENT_RATES["refactor"]:
                refactor_kb = dev.total_code_produced_kb * self.rng.uniform(0.01, 0.05)
                dev.total_refactored_kb += refactor_kb
                day_messages += 1
                day_events.append(DayEvent(
                    day=day, event_type="refactor",
                    node_address=dev.address,
                    detail=f"Refactoring: {refactor_kb:.0f} KB",
                    impact_kb=refactor_kb * 0.1,  # Refactoring az miktar yeni kod üretir
                ))
        
        # ─── 6. RAPORLAMA (aşağıdan yukarı) ─────────────────────────────
        # Her seviye bir üstüne rapor verir
        for level in range(self.hierarchy_depth, 0, -1):
            nodes_at_level = self.branch_factor ** level
            day_messages += nodes_at_level
        
        # ─── 7. SNAPSHOT TAMAMLA ─────────────────────────────────────────
        self.cumulative_code_kb += snapshot.code_produced_today_kb
        snapshot.cumulative_code_kb = self.cumulative_code_kb
        snapshot.progress_pct = (self.cumulative_code_kb / self.total_target_kb) * 100
        
        snapshot.cumulative_bugs = self.cumulative_bugs
        snapshot.cumulative_bugs_fixed = self.cumulative_bugs_fixed
        
        # Geliştirici durumları
        for dev in self.developers.values():
            if dev.status == DevStatus.ACTIVE:
                snapshot.active_devs += 1
            elif dev.status == DevStatus.SICK:
                snapshot.sick_devs += 1
            elif dev.status == DevStatus.VACATION:
                snapshot.vacation_devs += 1
            elif dev.status == DevStatus.BLOCKED:
                snapshot.blocked_devs += 1
            elif dev.status == DevStatus.BURNOUT:
                snapshot.burnout_devs += 1
        
        # Morale & fatigue ortalama
        morales = [d.morale for d in self.developers.values()]
        fatigues = [d.fatigue for d in self.developers.values()]
        snapshot.avg_morale = sum(morales) / len(morales)
        snapshot.avg_fatigue = sum(fatigues) / len(fatigues)
        
        snapshot.messages_today = day_messages
        snapshot.escalations_today = day_escalations
        snapshot.events_today = len(day_events)
        
        self.cumulative_messages += day_messages
        self.all_events.extend(day_events)
        
        return snapshot
    
    def _process_random_events(self, dev: Developer, day: int, events: list):
        """Rastgele olayları işle"""
        
        # Hastalanma
        if self.rng.random() < EVENT_RATES["sick_day"]:
            dev.status = DevStatus.SICK
            dev.status_days_remaining = self.rng.randint(1, 5)
            dev.streak_days = 0
            events.append(DayEvent(
                day=day, event_type="sick",
                node_address=dev.address,
                detail=f"Hasta - {dev.status_days_remaining} gün",
            ))
            return
        
        # Tatil
        if self.rng.random() < EVENT_RATES["vacation"]:
            dev.status = DevStatus.VACATION
            dev.status_days_remaining = self.rng.randint(3, 10)
            dev.streak_days = 0
            dev.fatigue = max(0, dev.fatigue - 0.3)  # Tatilde dinlenir
            dev.morale = min(1.5, dev.morale + 0.1)
            events.append(DayEvent(
                day=day, event_type="vacation",
                node_address=dev.address,
                detail=f"Tatil - {dev.status_days_remaining} gün",
            ))
            return
        
        # Tükenmişlik (yüksek yorgunluk varsa)
        if dev.fatigue > 0.8 and self.rng.random() < EVENT_RATES["burnout"]:
            dev.status = DevStatus.BURNOUT
            dev.status_days_remaining = self.rng.randint(5, 15)
            dev.streak_days = 0
            events.append(DayEvent(
                day=day, event_type="burnout",
                node_address=dev.address,
                detail=f"Tükenmişlik - {dev.status_days_remaining} gün ara",
            ))
            return
        
        # Bağımlılık bloğu
        if self.rng.random() < EVENT_RATES["dependency_block"]:
            dev.status = DevStatus.BLOCKED
            dev.status_days_remaining = self.rng.randint(1, 3)
            events.append(DayEvent(
                day=day, event_type="blocked",
                node_address=dev.address,
                detail=f"Bağımlılık bloğu - {dev.status_days_remaining} gün",
            ))
            return
        
        # Verimlilik patlaması
        if self.rng.random() < EVENT_RATES["breakthrough"]:
            dev.morale = min(1.5, dev.morale + 0.15)
            dev.fatigue = max(0, dev.fatigue - 0.1)
            events.append(DayEvent(
                day=day, event_type="breakthrough",
                node_address=dev.address,
                detail="Verimlilik patlaması! Moral yükseldi.",
            ))
        
        # Moral düşüşü (uzun süre çalışma)
        if dev.streak_days > 20:
            dev.morale = max(0.5, dev.morale - 0.01)
    
    # ─── Sprint Yönetimi ─────────────────────────────────────────────────
    
    def _finalize_sprint(self, end_day: int):
        """Sprint sonunu hesapla"""
        start_day = self.sprint_start_day
        sprint_days = [s for s in self.daily_snapshots 
                      if start_day <= s.day <= end_day]
        
        if not sprint_days:
            return
        
        report = SprintReport(
            sprint_number=self.current_sprint,
            start_day=start_day,
            end_day=end_day,
        )
        
        for snap in sprint_days:
            report.code_produced_kb += snap.code_produced_today_kb
            report.bugs_created += snap.bugs_today
            report.bugs_fixed += snap.bugs_fixed_today
            report.sick_days += snap.sick_devs
            report.vacation_days += snap.vacation_devs
            report.blocked_days += snap.blocked_devs
            report.total_messages += snap.messages_today
            report.escalations += snap.escalations_today
        
        # Sprint hedefi
        sprint_target = self.total_target_kb / (SIMULATION_DAYS / SPRINT_DAYS)
        report.code_target_kb = sprint_target
        report.plan_completion_pct = (report.code_produced_kb / sprint_target * 100) if sprint_target > 0 else 0
        
        # Son tarihteki aktif geliştiriciler
        last_snap = sprint_days[-1]
        report.active_developers = last_snap.active_devs
        report.cumulative_progress_pct = last_snap.progress_pct
        
        if report.active_developers > 0:
            effective_days = len([s for s in sprint_days if s.date and s.date.weekday() < 5])
            report.velocity_kb_per_dev = report.code_produced_kb / (report.active_developers * max(1, effective_days))
        
        # Tükenmişlik sayısı
        report.burnout_cases = sum(
            1 for e in self.all_events
            if e.event_type == "burnout" and start_day <= e.day <= end_day
        )
        
        # Kritik olaylar
        report.critical_events = [
            f"Gün {e.day}: [{e.event_type}] {e.node_address} - {e.detail}"
            for e in self.all_events
            if start_day <= e.day <= end_day 
            and e.event_type in ("critical_bug", "burnout", "breakthrough")
        ][:10]  # Max 10 önemli olay
        
        self.sprint_reports.append(report)
    
    # ─── Raporlama ───────────────────────────────────────────────────────
    
    def _generate_final_report(self) -> dict:
        """Yıl sonu özet raporu"""
        
        # Geliştirici performans dağılımı
        dev_stats = defaultdict(lambda: {
            "count": 0, "total_kb": 0, "bugs_created": 0,
            "bugs_fixed": 0, "reviews": 0,
        })
        
        top_producers = []
        for dev in self.developers.values():
            s = dev_stats[dev.skill]
            s["count"] += 1
            s["total_kb"] += dev.total_code_produced_kb
            s["bugs_created"] += dev.total_bugs_created
            s["bugs_fixed"] += dev.total_bugs_fixed
            s["reviews"] += dev.total_reviews_done
            
            top_producers.append((dev.address, dev.skill, dev.total_code_produced_kb))
        
        top_producers.sort(key=lambda x: x[2], reverse=True)
        
        # En iyi ve en kötü sprintler
        best_sprint = max(self.sprint_reports, key=lambda s: s.code_produced_kb,default=None)
        worst_sprint = min(self.sprint_reports, key=lambda s: s.code_produced_kb, default=None)
        
        # Günlük trend (aylık ortalamalara indir)
        monthly_avg = defaultdict(lambda: {"total_kb": 0, "days": 0, "bugs": 0})
        for snap in self.daily_snapshots:
            if snap.date:
                month_key = snap.date.strftime("%Y-%m")
                monthly_avg[month_key]["total_kb"] += snap.code_produced_today_kb
                monthly_avg[month_key]["days"] += 1
                monthly_avg[month_key]["bugs"] += snap.bugs_today
        
        return {
            "summary": {
                "project_size_gb": self.total_target_kb / (1024 * 1024),
                "total_days": SIMULATION_DAYS,
                "total_sprints": len(self.sprint_reports),
                "total_developers": self.num_developers,
                "hierarchy_depth": self.hierarchy_depth,
            },
            "production": {
                "total_code_produced_kb": self.cumulative_code_kb,
                "total_code_produced_gb": self.cumulative_code_kb / (1024 * 1024),
                "target_kb": self.total_target_kb,
                "target_gb": self.total_target_kb / (1024 * 1024),
                "completion_pct": (self.cumulative_code_kb / self.total_target_kb) * 100,
                "avg_daily_production_kb": self.cumulative_code_kb / SIMULATION_DAYS,
                "avg_daily_per_dev_kb": self.cumulative_code_kb / (self.num_developers * SIMULATION_DAYS),
            },
            "quality": {
                "total_bugs_created": self.cumulative_bugs,
                "total_bugs_fixed": self.cumulative_bugs_fixed,
                "open_bugs": self.cumulative_bugs - self.cumulative_bugs_fixed,
                "bug_rate_per_1000kb": (self.cumulative_bugs / max(1, self.cumulative_code_kb)) * 1000,
                "fix_rate_pct": (self.cumulative_bugs_fixed / max(1, self.cumulative_bugs)) * 100,
            },
            "people": {
                "skill_distribution": dict(dev_stats),
                "top_10_producers": [
                    {"address": a, "skill": s, "produced_kb": round(k, 1)}
                    for a, s, k in top_producers[:10]
                ],
                "bottom_10_producers": [
                    {"address": a, "skill": s, "produced_kb": round(k, 1)}
                    for a, s, k in top_producers[-10:]
                ],
            },
            "sprints": {
                "total_sprints": len(self.sprint_reports),
                "best_sprint": {
                    "number": best_sprint.sprint_number if best_sprint else 0,
                    "code_kb": best_sprint.code_produced_kb if best_sprint else 0,
                } if best_sprint else None,
                "worst_sprint": {
                    "number": worst_sprint.sprint_number if worst_sprint else 0,
                    "code_kb": worst_sprint.code_produced_kb if worst_sprint else 0,
                } if worst_sprint else None,
            },
            "communication": {
                "total_messages": self.cumulative_messages,
                "total_events": len(self.all_events),
                "events_by_type": dict(
                    sorted(
                        defaultdict(int, {
                            e.event_type: sum(1 for x in self.all_events if x.event_type == e.event_type)
                            for e in self.all_events
                        }).items(),
                        key=lambda x: -x[1]
                    )
                ),
            },
            "monthly_trend": {
                month: {
                    "production_gb": data["total_kb"] / (1024 * 1024),
                    "daily_avg_kb": data["total_kb"] / max(1, data["days"]),
                    "bugs": data["bugs"],
                }
                for month, data in sorted(monthly_avg.items())
            },
        }
