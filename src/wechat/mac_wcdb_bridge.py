"""macOS reader bridge: WCDB_KEY + pure-Python decrypt, WeFlow-shaped API.

MacHybridBackend historically required WeFlow's ``libWCDB.dylib`` and an
``all_keys.json`` produced by WeFlow's own key step.  Users who obtained a
64-hex ``WCDB_KEY`` on Windows (including a Windows VM on the same Mac) could
not use that key with the default macOS backend.

This module adapts :class:`WcdbNativeClient` (SQLCipher via ``db_crypto``) to
the small interface MacHybridBackend already calls: ``health``,
``get_new_messages``, ``get_sessions``, ``get_chatrooms``, ``get_contacts``.
No process memory access and no third-party key helpers.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 200
HEX_KEY_LEN = 64


def wcdb_key_configured() -> bool:
    """Return True when a syntactically plausible WCDB_KEY is in the environment."""
    key = (os.getenv("WCDB_KEY") or "").strip()
    if len(key) != HEX_KEY_LEN:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in key)


class MacWcdbBridgeClient:
    """WeFlow-compatible client backed by WcdbNativeClient + WCDB_KEY."""

    def __init__(self, native_client: Any = None):
        self._native = native_client
        self._last_error = ""
        self._opened = False
        self._chat_title_cache: dict[str, str] = {}
        self._display_name_cache: dict[str, str] = {}

    def health(self) -> bool:
        try:
            if not self._ensure_open():
                return False
            sessions = self._native.get_sessions(limit=1)
            return isinstance(sessions, list)
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            logger.debug("macOS WCDB bridge health failed: %s", exc)
            return False

    def get_new_messages(
        self,
        state: dict | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> dict:
        if not self._ensure_open():
            raise RuntimeError(self._last_error or "macOS WCDB bridge is not ready")

        safe_limit = max(1, int(limit or DEFAULT_LIMIT))
        old_state = {
            str(k): int(v)
            for k, v in (state or {}).items()
            if _can_int(v)
        }
        sessions = self._native.get_sessions(limit=500) or []
        group_sessions = [
            row for row in sessions
            if str(row.get("username") or "").endswith("@chatroom")
        ]
        self._hydrate_titles([
            str(row.get("username") or "").strip()
            for row in group_sessions
            if str(row.get("username") or "").strip()
        ])

        new_state: dict[str, int] = {}
        changed: list[str] = []
        fallback = int(time.time()) - 24 * 3600
        for row in group_sessions:
            username = str(row.get("username") or "").strip()
            if not username:
                continue
            ts = int(row.get("last_timestamp") or row.get("sort_timestamp") or 0)
            if ts <= 0:
                ts = fallback
            new_state[username] = ts
            if ts > old_state.get(username, fallback):
                changed.append(username)

        out: list[dict[str, Any]] = []
        for username in changed:
            last = old_state.get(username, fallback)
            try:
                rows = self._native.get_messages(username, limit=safe_limit * 3, offset=0) or []
            except Exception as exc:  # noqa: BLE001
                logger.debug("bridge get_messages(%s) failed: %s", username[:24], exc)
                continue
            for row in rows:
                normalized = self._message_to_source_row(username, row)
                if not normalized:
                    continue
                if int(normalized.get("timestamp") or 0) <= last:
                    continue
                out.append(normalized)
                if len(out) >= safe_limit:
                    break
            if len(out) >= safe_limit:
                break

        out.sort(key=lambda item: int(item.get("timestamp") or 0))
        return {
            "count": len(out),
            "messages": out,
            "new_state": new_state,
        }

    def get_sessions(self, limit: int = 500) -> dict:
        if not self._ensure_open():
            raise RuntimeError(self._last_error or "macOS WCDB bridge is not ready")
        rows = self._native.get_sessions(limit=limit) or []
        usernames = [str(r.get("username") or "").strip() for r in rows if r.get("username")]
        self._hydrate_titles([u for u in usernames if u.endswith("@chatroom")])
        self._hydrate_contacts([u for u in usernames if u and not u.endswith("@chatroom")])
        sessions = []
        for row in rows[: max(1, int(limit or 500))]:
            username = str(row.get("username") or "").strip()
            if not username:
                continue
            display = (
                self._chat_title_cache.get(username)
                or self._display_name_cache.get(username)
                or str(row.get("displayName") or row.get("display_name") or row.get("nickname") or "")
                or username
            )
            is_group = username.endswith("@chatroom")
            sessions.append({
                **row,
                "username": username,
                "chat": display,
                "display": display,
                "nickname": display,
                "is_group": is_group,
                "chat_type": "group" if is_group else "private",
            })
        return {"count": len(sessions), "sessions": sessions}

    def get_chatrooms(self, limit: int = 500) -> dict:
        if not self._ensure_open():
            raise RuntimeError(self._last_error or "macOS WCDB bridge is not ready")
        contacts = self._native.get_contacts(limit=max(1, int(limit or 500)) * 2) or []
        chatrooms = []
        for row in contacts:
            username = str(row.get("username") or row.get("userName") or "").strip()
            if not username.endswith("@chatroom"):
                continue
            display = (
                str(row.get("remark") or "").strip()
                or str(row.get("nick_name") or row.get("nickName") or row.get("nickname") or "").strip()
                or username
            )
            self._chat_title_cache[username] = display
            chatrooms.append({
                "name": username,
                "username": username,
                "display": display,
                "remark": str(row.get("remark") or "").strip(),
                "nickname": str(row.get("nick_name") or row.get("nickName") or row.get("nickname") or "").strip(),
            })
        if not chatrooms:
            for row in self.get_sessions(limit=limit).get("sessions", []):
                username = str(row.get("username") or "").strip()
                if not username.endswith("@chatroom"):
                    continue
                display = str(row.get("display") or row.get("chat") or username).strip()
                chatrooms.append({
                    "name": username,
                    "username": username,
                    "display": display,
                    "remark": "",
                    "nickname": display if display != username else "",
                })
        return {"count": len(chatrooms), "chatrooms": chatrooms[: max(1, int(limit or 500))]}

    def get_contacts(self, limit: int = 500) -> dict:
        if not self._ensure_open():
            raise RuntimeError(self._last_error or "macOS WCDB bridge is not ready")
        rows = self._native.get_contacts(limit=max(1, int(limit or 500))) or []
        contacts = []
        for row in rows:
            username = str(row.get("username") or row.get("userName") or "").strip()
            if not username:
                continue
            display = (
                str(row.get("remark") or "").strip()
                or str(row.get("nick_name") or row.get("nickName") or row.get("nickname") or "").strip()
                or username
            )
            self._display_name_cache[username] = display
            contacts.append({
                "username": username,
                "name": username,
                "display": display,
                "remark": str(row.get("remark") or "").strip(),
                "nickname": str(row.get("nick_name") or row.get("nickName") or row.get("nickname") or "").strip(),
                "alias": str(row.get("alias") or row.get("Alias") or "").strip(),
            })
        return {"count": len(contacts), "contacts": contacts}

    def close(self) -> None:
        native = self._native
        self._native = None
        self._opened = False
        if native is not None:
            closer = getattr(native, "close", None)
            if callable(closer):
                try:
                    closer()
                except Exception:  # noqa: BLE001
                    pass

    # ── internals ──────────────────────────────────────────────────

    def _ensure_open(self) -> bool:
        if self._opened and self._native is not None:
            return True
        if not wcdb_key_configured():
            self._last_error = (
                "未配置 WCDB_KEY。请在 Windows（实体机或本机虚拟机）用摘星自动提取后，"
                "粘贴到 macOS「手动配置」。"
            )
            return False
        try:
            if self._native is None:
                from .wcdb_client import WcdbNativeClient
                self._native = WcdbNativeClient()
            self._native.init()
            self._native.open()
            self._opened = True
            self._last_error = ""
            logger.info("macOS WCDB bridge ready (pure-Python reader + WCDB_KEY)")
            return True
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            self._opened = False
            logger.warning("macOS WCDB bridge open failed: %s", exc)
            return False

    def _hydrate_titles(self, usernames: list[str]) -> None:
        missing = [u for u in usernames if u and u not in self._chat_title_cache]
        if not missing:
            return
        try:
            names = self._native.get_display_names(missing) or {}
        except Exception as exc:  # noqa: BLE001
            logger.debug("bridge get_display_names failed: %s", exc)
            return
        for username, title in names.items():
            text = str(title or "").strip()
            if text:
                self._chat_title_cache[str(username)] = text

    def _hydrate_contacts(self, usernames: list[str]) -> None:
        missing = [u for u in usernames if u and u not in self._display_name_cache]
        if not missing:
            return
        try:
            names = self._native.get_display_names(missing) or {}
        except Exception as exc:  # noqa: BLE001
            logger.debug("bridge contact names failed: %s", exc)
            return
        for username, title in names.items():
            text = str(title or "").strip()
            if text:
                self._display_name_cache[str(username)] = text

    def _message_to_source_row(self, chat_id: str, row: dict[str, Any]) -> dict[str, Any] | None:
        is_send = int(row.get("is_send") if row.get("is_send") is not None else -1)
        if is_send < 0:
            status = int(row.get("status") or 0)
            is_send = 1 if status == 2 else 0
        if is_send == 1:
            return None
        ts = int(row.get("create_time") or row.get("createTime") or row.get("timestamp") or 0)
        if ts <= 0:
            return None
        local_id = int(row.get("local_id") or row.get("localId") or 0)
        local_type = int(row.get("local_type") or row.get("localType") or row.get("msg_type") or 1)
        sender = str(
            row.get("sender_username")
            or row.get("senderUsername")
            or row.get("sender")
            or ""
        ).strip()
        content = str(row.get("message_content") or row.get("content") or "").strip()
        if chat_id.endswith("@chatroom") and content and ":\n" in content[:80]:
            # Group messages often prefix "wxid:\nbody"
            head, _, body = content.partition(":\n")
            if head and not body.startswith("<"):
                if not sender:
                    sender = head.strip()
                content = body.strip()
        if local_type != 1:
            content = _message_type_label(local_type)
        if not content:
            content = _message_type_label(local_type)
        display = self._chat_title_cache.get(chat_id) or chat_id
        if sender and sender not in self._display_name_cache:
            self._hydrate_contacts([sender])
        sender_display = self._display_name_cache.get(sender) or sender or "unknown"
        return {
            "timestamp": ts,
            "sender": sender_display,
            "sender_name": sender_display,
            "sender_id": sender or sender_display,
            "type": _message_type_name(local_type),
            "content": content,
            "local_id": local_id,
            "chat": display,
            "username": chat_id,
            "is_group": chat_id.endswith("@chatroom"),
            "chat_type": "group" if chat_id.endswith("@chatroom") else "private",
        }


def _can_int(value: Any) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def _message_type_name(local_type: int) -> str:
    mapping = {
        1: "text",
        3: "image",
        34: "voice",
        42: "card",
        43: "video",
        47: "emoji",
        48: "location",
        49: "app",
        10000: "system",
    }
    return mapping.get(int(local_type or 0), f"type_{local_type}")


def _message_type_label(local_type: int) -> str:
    labels = {
        3: "[图片]",
        34: "[语音]",
        42: "[名片]",
        43: "[视频]",
        47: "[表情]",
        48: "[位置]",
        49: "[应用消息]",
        10000: "[系统消息]",
    }
    return labels.get(int(local_type or 0), f"[消息类型 {local_type}]")
