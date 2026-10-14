"""Tests for macOS WCDB_KEY bridge selection (no real WeChat key required)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from src.wechat.mac_wcdb_bridge import MacWcdbBridgeClient, wcdb_key_configured
from src.wechat import mac_hybrid_backend as hybrid


def test_wcdb_key_configured_requires_64_hex(monkeypatch):
    monkeypatch.delenv("WCDB_KEY", raising=False)
    assert wcdb_key_configured() is False
    monkeypatch.setenv("WCDB_KEY", "abcd")
    assert wcdb_key_configured() is False
    monkeypatch.setenv("WCDB_KEY", "g" * 64)
    assert wcdb_key_configured() is False
    monkeypatch.setenv("WCDB_KEY", "a" * 64)
    assert wcdb_key_configured() is True


def test_default_mac_reader_prefers_bridge_when_key_set(monkeypatch):
    monkeypatch.setenv("WCDB_KEY", "b" * 64)
    client = hybrid._default_mac_reader()
    assert isinstance(client, MacWcdbBridgeClient)


def test_default_mac_reader_falls_back_to_weflow_without_key(monkeypatch):
    monkeypatch.delenv("WCDB_KEY", raising=False)
    from src.wechat.mac_weflow_client import MacWeFlowClient
    client = hybrid._default_mac_reader()
    assert isinstance(client, MacWeFlowClient)


def test_bridge_message_normalization_skips_outgoing():
    native = MagicMock()
    bridge = MacWcdbBridgeClient(native_client=native)
    bridge._opened = True
    outgoing = {
        "is_send": 1,
        "create_time": 100,
        "local_id": 1,
        "local_type": 1,
        "sender_username": "me",
        "message_content": "hi",
    }
    assert bridge._message_to_source_row("x@chatroom", outgoing) is None

    incoming = {
        "is_send": 0,
        "create_time": 200,
        "local_id": 2,
        "local_type": 1,
        "sender_username": "wxid_other",
        "message_content": "wxid_other:\nhello",
    }
    row = bridge._message_to_source_row("x@chatroom", incoming)
    assert row is not None
    assert row["content"] == "hello"
    assert row["username"] == "x@chatroom"
    assert row["is_group"] is True


def test_bridge_ensure_open_without_key_sets_error(monkeypatch):
    monkeypatch.delenv("WCDB_KEY", raising=False)
    bridge = MacWcdbBridgeClient()
    assert bridge._ensure_open() is False
    assert "WCDB_KEY" in bridge._last_error
