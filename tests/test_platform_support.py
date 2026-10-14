"""Cross-platform path, lock, and packaging-plan tests."""

from pathlib import Path

import pytest

from packaging.pyi_common import collect, hiddenimports
from src.platform_support import (
    acquire_single_instance,
    default_wechat_backend,
    discover_wechat_accounts,
    hidden_window_kwargs,
    kvcomm_dirs,
    supports_key_hook,
    try_lock_file,
    unlock_file,
)
from src.wechat.extract_key import extract_wcdb_key


def test_hidden_window_kwargs_omit_creationflags_off_windows():
    kwargs = hidden_window_kwargs()
    if __import__("sys").platform == "win32":
        assert "creationflags" in kwargs
    else:
        assert kwargs == {}


def test_default_backend_matches_os():
    system = __import__("platform").system()
    if system == "Darwin":
        assert default_wechat_backend() == "mac_hybrid"
    else:
        assert default_wechat_backend() == "wcdb"


def test_key_hook_is_windows_only():
    assert supports_key_hook() is (__import__("sys").platform == "win32")


def test_extract_key_degrades_off_windows():
    if __import__("sys").platform == "win32":
        pytest.skip("Windows still runs the DLL hook")
    phases = []
    key = extract_wcdb_key(on_progress=lambda phase, message: phases.append((phase, message)))
    assert key is None
    assert phases and phases[0][0] == "unsupported"


def test_discover_wechat_account_in_custom_dir(tmp_path: Path):
    account = tmp_path / "wxid_demo"
    session = account / "db_storage" / "session"
    session.mkdir(parents=True)
    (session / "session.db").write_bytes(b"")
    hits = discover_wechat_accounts([tmp_path])
    assert hits
    assert hits[0].wxid == "wxid_demo"
    assert hits[0].session_db == session / "session.db"


def test_kvcomm_dirs_include_windows_appdata(monkeypatch):
    monkeypatch.setenv("APPDATA", r"C:\Users\demo\AppData\Roaming")
    monkeypatch.setattr("src.platform_support.is_windows", lambda: True)
    dirs = [str(path) for path in kvcomm_dirs()]
    assert any(path.replace("\\", "/").endswith("Tencent/xwechat/net/kvcomm") for path in dirs)
    assert any(path.replace("\\", "/").endswith("Tencent/xwechat/net_1/kvcomm") for path in dirs)


def test_file_lock_roundtrip(tmp_path: Path):
    lock_path = tmp_path / "app.lock"
    first = open(lock_path, "w")
    second = open(lock_path, "a+")
    try:
        assert try_lock_file(first) is True
        # A second description in this process may or may not block, depending
        # on the OS. The first lock must unlock cleanly either way.
        unlock_file(first)
        assert try_lock_file(second) is True
        unlock_file(second)
    finally:
        first.close()
        second.close()


def test_single_instance_lock_acquired():
    assert acquire_single_instance("wx-assist-test-platform-support") is True


def test_wcdb_backend_imports_off_windows():
    from src.wechat.wcdb_backend import WcdbBackend

    backend = WcdbBackend(groups=["demo"])
    assert backend._window is not None


def test_collect_plan_for_each_desktop_os(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "version.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8")
    dist = tmp_path / "ui" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / ".env.example").write_text("A=1\n", encoding="utf-8")
    (tmp_path / "favicon.ico").write_bytes(b"ico")
    png_dir = tmp_path / "ui" / "public"
    png_dir.mkdir()
    (png_dir / "favicon.png").write_bytes(b"png")

    linux = collect(tmp_path, with_rag=False, exe_name="wx-assist_no_rag", system="Linux")
    assert linux["bundle"] is None
    assert linux["exe"]["name"] == "wx-assist_no_rag"
    assert "version" not in linux["exe"]
    assert linux["analysis"]["binaries"] == []
    assert "numpy" in linux["analysis"]["excludes"]
    assert "pystray._gtk" in linux["analysis"]["hiddenimports"]
    assert "webview.platforms.edgechromium" not in linux["analysis"]["hiddenimports"]

    mac = collect(tmp_path, with_rag=True, exe_name="wx-assist", system="Darwin")
    assert mac["bundle"]["name"] == "wx-assist.app"
    assert "chromadb" in mac["analysis"]["hiddenimports"]
    assert "numpy" not in mac["analysis"]["excludes"]
    assert "pystray._darwin" in mac["analysis"]["hiddenimports"]

    assert "pystray._win32" in hiddenimports(with_rag=False, system="Windows")
    assert "uiautomation" in hiddenimports(with_rag=False, system="Windows")


def test_config_default_backend_follows_platform(monkeypatch):
    monkeypatch.delenv("WECHAT_BACKEND", raising=False)
    from src.config import load_config

    assert load_config().wechat_backend == default_wechat_backend()
