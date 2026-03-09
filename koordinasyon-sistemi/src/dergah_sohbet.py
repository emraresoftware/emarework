"""
Dergah Sohbet Odası — Derviş İletişim Sistemi
==============================================

Tüm Emare dervişlerinin birbiriyle sohbet edebildiği,
dosya paylaşabildiği ve GitHub issue'ları görebildiği
merkezi iletişim modülü.

Özellikler:
- Genel dergah sohbet odası (tüm dervişler)
- Birebir derviş mesajları
- Sistem duyuruları
- GitHub entegrasyonu (issue/PR özeti)
- Dosya paylaşım referansları
- Mesaj geçmişi ve arama
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog

logger = structlog.get_logger()


class DergahMessageType(str, Enum):
    """Dergah mesaj tipleri."""
    CHAT = "chat"              # Normal sohbet
    SYSTEM = "system"          # Sistem duyurusu
    GITHUB = "github"          # GitHub bildirimi
    FILE_SHARE = "file_share"  # Dosya paylaşımı
    TASK_UPDATE = "task_update" # Görev güncelleme
    DEPLOY = "deploy"          # Deploy bildirimi
    ALERT = "alert"            # Uyarı/alarm


class DergahRoom(str, Enum):
    """Dergah odaları."""
    GENEL = "genel"                # Tüm dervişler
    BACKEND = "backend"            # Backend dervişleri
    FRONTEND = "frontend"          # Frontend dervişleri
    ALTYAPI = "altyapi"            # Altyapı dervişleri
    GUVENLIK = "guvenlik"          # Güvenlik dervişleri
    AI = "ai"                      # AI dervişleri
    ACIL = "acil"                  # Acil durum odası


@dataclass
class DergahMessage:
    """Dergah sohbet mesajı."""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    room: str = "genel"
    sender_id: str = ""              # Derviş ID (emare-asistan, emarecloud vb.)
    sender_name: str = ""            # Görünen ad
    sender_icon: str = "🧙‍♂️"
    message_type: str = "chat"       # DergahMessageType
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)  # Ek veri (github_url, file_path, vb.)
    reply_to: Optional[str] = None   # Yanıt verilen mesaj uid
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji → [sender_ids]
    pinned: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "uid": self.uid,
            "room": self.room,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "sender_icon": self.sender_icon,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "reply_to": self.reply_to,
            "reactions": self.reactions,
            "pinned": self.pinned,
            "created_at": self.created_at,
        }


class DergahSohbet:
    """
    Dergah Sohbet Odası — Derviş İletişim Merkezi.
    
    In-memory mesaj deposu + oda yönetimi.
    """

    def __init__(self, max_messages_per_room: int = 500):
        self.max_messages = max_messages_per_room
        # room_name → [DergahMessage]
        self.rooms: Dict[str, List[DergahMessage]] = {
            room.value: [] for room in DergahRoom
        }
        # uid → DergahMessage (hızlı erişim)
        self._message_index: Dict[str, DergahMessage] = {}
        # dervis_id → son görülme zamanı
        self._online_status: Dict[str, str] = {}
        # dervis_id → {room → last_read_uid}
        self._read_cursors: Dict[str, Dict[str, str]] = {}

        logger.info("dergah_initialized", rooms=len(self.rooms))

        # Başlangıç mesajı
        self._add_system_message(
            "genel",
            "🕌 Dergah Sohbet Odası açıldı. Hoş geldiniz dervişler!"
        )

    # ── Mesaj Gönderme ────────────────────────────────────────────────────────

    def send_message(
        self,
        room: str,
        sender_id: str,
        sender_name: str,
        content: str,
        sender_icon: str = "🧙‍♂️",
        message_type: str = "chat",
        metadata: Optional[Dict] = None,
        reply_to: Optional[str] = None,
    ) -> DergahMessage:
        """Odaya mesaj gönder."""
        if room not in self.rooms:
            self.rooms[room] = []

        msg = DergahMessage(
            room=room,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_icon=sender_icon,
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            reply_to=reply_to,
        )

        self.rooms[room].append(msg)
        self._message_index[msg.uid] = msg

        # Max mesaj sınırı
        if len(self.rooms[room]) > self.max_messages:
            removed = self.rooms[room].pop(0)
            self._message_index.pop(removed.uid, None)

        # Online durumunu güncelle
        self._online_status[sender_id] = datetime.now().isoformat()

        logger.info("dergah_message_sent", room=room, sender=sender_id, type=message_type)
        return msg

    def _add_system_message(self, room: str, content: str, metadata: Optional[Dict] = None) -> DergahMessage:
        """Sistem mesajı ekle."""
        return self.send_message(
            room=room,
            sender_id="system",
            sender_name="Dergah Sistemi",
            sender_icon="🕌",
            message_type="system",
            content=content,
            metadata=metadata,
        )

    # ── GitHub Entegrasyonu ───────────────────────────────────────────────────

    def notify_github_event(
        self,
        event_type: str,  # push, issue, pr, webhook
        repo_name: str,
        description: str,
        url: str = "",
        actor: str = "",
    ) -> DergahMessage:
        """GitHub olayını dergaha bildir."""
        icon_map = {
            "push": "📦",
            "issue": "🐛",
            "pr": "🔀",
            "webhook": "🔔",
            "deploy": "🚀",
        }
        icon = icon_map.get(event_type, "📢")
        content = f"{icon} **{repo_name}** — {description}"
        if actor:
            content += f" (by {actor})"

        return self.send_message(
            room="genel",
            sender_id="github-bot",
            sender_name="GitHub Bot",
            sender_icon="🐙",
            message_type="github",
            content=content,
            metadata={
                "event_type": event_type,
                "repo": repo_name,
                "url": url,
                "actor": actor,
            },
        )

    # ── Dosya Paylaşımı ──────────────────────────────────────────────────────

    def share_file(
        self,
        room: str,
        sender_id: str,
        sender_name: str,
        file_path: str,
        file_size: int = 0,
        description: str = "",
        sender_icon: str = "🧙‍♂️",
    ) -> DergahMessage:
        """Dosya paylaşım referansı gönder."""
        file_name = file_path.split("/")[-1]
        size_str = f"{file_size / 1024:.1f} KB" if file_size else "?"
        content = f"📎 **{file_name}** ({size_str})"
        if description:
            content += f" — {description}"

        return self.send_message(
            room=room,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_icon=sender_icon,
            message_type="file_share",
            content=content,
            metadata={"file_path": file_path, "file_size": file_size, "file_name": file_name},
        )

    # ── Deploy Bildirimi ──────────────────────────────────────────────────────

    def notify_deploy(
        self,
        project_id: str,
        project_name: str,
        version: str = "",
        status: str = "success",
    ) -> DergahMessage:
        """Deploy bildirimini dergaha gönder."""
        icon = "🚀" if status == "success" else "❌"
        content = f"{icon} **{project_name}** deploy {'başarılı' if status == 'success' else 'başarısız'}"
        if version:
            content += f" (v{version})"

        return self.send_message(
            room="genel",
            sender_id=project_id,
            sender_name=project_name,
            sender_icon=icon,
            message_type="deploy",
            content=content,
            metadata={"project_id": project_id, "version": version, "status": status},
        )

    # ── Mesaj Okuma ───────────────────────────────────────────────────────────

    def get_messages(
        self,
        room: str = "genel",
        limit: int = 50,
        before: Optional[str] = None,  # before this uid
        after: Optional[str] = None,   # after this uid
        message_type: Optional[str] = None,
    ) -> List[Dict]:
        """Oda mesajlarını getir."""
        messages = self.rooms.get(room, [])

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        if after:
            idx = next((i for i, m in enumerate(messages) if m.uid == after), -1)
            if idx >= 0:
                messages = messages[idx + 1:]

        if before:
            idx = next((i for i, m in enumerate(messages) if m.uid == before), len(messages))
            messages = messages[:idx]

        return [m.to_dict() for m in messages[-limit:]]

    def get_message(self, uid: str) -> Optional[Dict]:
        """Tek mesaj getir."""
        msg = self._message_index.get(uid)
        return msg.to_dict() if msg else None

    # ── Reaksiyon ─────────────────────────────────────────────────────────────

    def add_reaction(self, message_uid: str, emoji: str, sender_id: str) -> bool:
        """Mesaja reaksiyon ekle."""
        msg = self._message_index.get(message_uid)
        if not msg:
            return False
        if emoji not in msg.reactions:
            msg.reactions[emoji] = []
        if sender_id not in msg.reactions[emoji]:
            msg.reactions[emoji].append(sender_id)
        return True

    def remove_reaction(self, message_uid: str, emoji: str, sender_id: str) -> bool:
        """Reaksiyonu kaldır."""
        msg = self._message_index.get(message_uid)
        if not msg or emoji not in msg.reactions:
            return False
        msg.reactions[emoji] = [s for s in msg.reactions[emoji] if s != sender_id]
        if not msg.reactions[emoji]:
            del msg.reactions[emoji]
        return True

    # ── Pin / Unpin ───────────────────────────────────────────────────────────

    def pin_message(self, uid: str) -> bool:
        msg = self._message_index.get(uid)
        if not msg:
            return False
        msg.pinned = True
        return True

    def unpin_message(self, uid: str) -> bool:
        msg = self._message_index.get(uid)
        if not msg:
            return False
        msg.pinned = False
        return True

    def get_pinned(self, room: str = "genel") -> List[Dict]:
        return [m.to_dict() for m in self.rooms.get(room, []) if m.pinned]

    # ── Online Durumu ─────────────────────────────────────────────────────────

    def heartbeat(self, dervis_id: str) -> None:
        """Dervişin online olduğunu bildir."""
        self._online_status[dervis_id] = datetime.now().isoformat()

    def get_online_dervishes(self, timeout_minutes: int = 5) -> List[str]:
        """Son X dakikada aktif dervişleri getir."""
        cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
        return [
            d_id for d_id, ts in self._online_status.items()
            if datetime.fromisoformat(ts) > cutoff
        ]

    # ── Oda Listesi ───────────────────────────────────────────────────────────

    def get_rooms(self) -> List[Dict]:
        """Tüm odaları ve mesaj sayılarını getir."""
        room_info = {
            "genel": {"icon": "🕌", "desc": "Tüm dervişler"},
            "backend": {"icon": "⚙️", "desc": "Backend dervişleri"},
            "frontend": {"icon": "🎨", "desc": "Frontend dervişleri"},
            "altyapi": {"icon": "🏗️", "desc": "Altyapı dervişleri"},
            "guvenlik": {"icon": "🛡️", "desc": "Güvenlik dervişleri"},
            "ai": {"icon": "🤖", "desc": "AI dervişleri"},
            "acil": {"icon": "🚨", "desc": "Acil durum odası"},
        }
        result = []
        for room_name, messages in self.rooms.items():
            info = room_info.get(room_name, {"icon": "💬", "desc": room_name})
            last_msg = messages[-1].to_dict() if messages else None
            result.append({
                "name": room_name,
                "icon": info["icon"],
                "description": info["desc"],
                "message_count": len(messages),
                "last_message": last_msg,
            })
        return result

    # ── Arama ─────────────────────────────────────────────────────────────────

    def search_messages(self, query: str, room: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Mesajlarda arama yap."""
        query_lower = query.lower()
        results = []

        rooms_to_search = [room] if room else list(self.rooms.keys())
        for r in rooms_to_search:
            for msg in reversed(self.rooms.get(r, [])):
                if query_lower in msg.content.lower() or query_lower in msg.sender_name.lower():
                    results.append(msg.to_dict())
                    if len(results) >= limit:
                        return results
        return results

    # ── İstatistikler ─────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Dergah istatistikleri."""
        total = sum(len(msgs) for msgs in self.rooms.values())
        by_type: Dict[str, int] = {}
        by_sender: Dict[str, int] = {}

        for msgs in self.rooms.values():
            for m in msgs:
                by_type[m.message_type] = by_type.get(m.message_type, 0) + 1
                by_sender[m.sender_id] = by_sender.get(m.sender_id, 0) + 1

        top_senders = sorted(by_sender.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_messages": total,
            "rooms": {name: len(msgs) for name, msgs in self.rooms.items()},
            "by_type": by_type,
            "top_senders": [{
                "sender_id": s[0],
                "count": s[1],
            } for s in top_senders],
            "online_count": len(self.get_online_dervishes()),
            "pinned_count": sum(
                1 for msgs in self.rooms.values() for m in msgs if m.pinned
            ),
        }

    # ── Mesaj Silme ───────────────────────────────────────────────────────────

    def delete_message(self, uid: str) -> bool:
        """Mesajı sil."""
        msg = self._message_index.pop(uid, None)
        if not msg:
            return False
        self.rooms[msg.room] = [m for m in self.rooms[msg.room] if m.uid != uid]
        return True


# ─── Singleton ────────────────────────────────────────────────────────────────

_dergah_instance: Optional[DergahSohbet] = None

def get_dergah() -> DergahSohbet:
    """Singleton dergah instance'ı döndür."""
    global _dergah_instance
    if _dergah_instance is None:
        _dergah_instance = DergahSohbet()
    return _dergah_instance
