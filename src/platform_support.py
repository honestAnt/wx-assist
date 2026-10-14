"""Portable OS helpers for paths, process checks, and desktop integration.

Windows keeps the existing WeChat client integration (key hook, Win32
window send, named mutex, WebView2). macOS and Linux use the same entry
points and skip features that need Windows APIs.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple


_SINGLE_INSTANCE: dict = {}


def system_name() -> str:
    """Return ``Windows``, ``Darwin``, or ``Linux`` (or another ``platform.system()`` value)."""
    return platform.system()


def is_windows() -> bool:
    return system_name() == "Windows"


def is_macos() -> bool:
    return system_name() == "Darwin"


def is_linux() -> bool:
    return system_name() == "Linux"


def supports_key_hook() -> bool:
    """Automatic WeChat key extraction uses a Windows DLL."""
    return is_windows()


def supports_window_send() -> bool:
    """Sending by driving the WeChat window is implemented for Win32 only."""
    return is_windows()


def supports_in_place_update() -> bool:
    """The packaged auto-updater swaps a Windows executable via a helper bat."""
    return is_windows()


def default_wechat_backend() -> str:
    """Backend used when ``WECHAT_BACKEND`` is unset.

    Windows and Linux read the local database through the pure-Python
    WCDB client (``wcdb``). macOS uses the existing hybrid reader.
    """
    if is_macos():
        return "mac_hybrid"
    return "wcdb"


def preferred_webview_gui() -> str | None:
    """pywebview GUI backend. ``None`` lets pywebview choose (Linux GTK/Qt)."""
    if is_windows():
        return "edgechromium"
    if is_macos():
        return "cocoa"
    return None


def hidden_window_kwargs() -> dict:
    """``subprocess`` kwargs that hide a console window on Windows.

    ``creationflags`` is rejected on non-Windows interpreters, so callers
    must unpack this dict instead of always passing the argument.
    """
    if is_windows():
        return {"creationflags": 0x08000000}  # CREATE_NO_WINDOW
    return {}


def documents_dir() -> Path:
    """The user's Documents folder, including Windows known-folder redirection."""
    if is_windows():
        try:
            import ctypes

            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf)  # CSIDL_PERSONAL
            if buf.value:
                return Path(buf.value)
        except Exception:
            pass
        profile = os.environ.get("USERPROFILE", "").strip()
        if profile:
            return Path(profile) / "Documents"
    xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR", "").strip()
    if xdg_docs:
        return Path(xdg_docs).expanduser()
    return Path.home() / "Documents"


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        try:
            key = str(path.expanduser())
        except Exception:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(Path(key))
    return out


def default_wechat_data_dirs() -> list[Path]:
    """Parent directories that may contain ``wxid_*`` account folders.

    These are search locations only. A directory is used when it actually
    contains a WeChat database; nothing here decrypts or hooks a client.
    """
    home = Path.home()
    docs = documents_dir()
    candidates = [
        docs / "xwechat_files",
        docs / "WeChat Files",
        home / "Documents" / "xwechat_files",
        home / "Documents" / "WeChat Files",
    ]
    if is_macos():
        container = home / "Library" / "Containers" / "com.tencent.xinWeChat" / "Data"
        candidates.extend([
            container / "Documents" / "xwechat_files",
            container / "Documents" / "WeChat Files",
            container / "Library" / "Application Support" / "com.tencent.xinWeChat",
        ])
    if not is_windows():
        candidates.extend([
            home / "xwechat_files",
            home / ".xwechat" / "xwechat_files",
            home / ".local" / "share" / "xwechat_files",
        ])
        wine_users = home / ".wine" / "drive_c" / "users"
        if wine_users.is_dir():
            try:
                user_dirs = [p for p in wine_users.iterdir() if p.is_dir()]
            except OSError:
                user_dirs = []
            for user_dir in user_dirs:
                candidates.append(user_dir / "Documents" / "xwechat_files")
                candidates.append(user_dir / "Documents" / "WeChat Files")
                candidates.append(user_dir / "My Documents" / "WeChat Files")
    return _unique_paths(candidates)


def kvcomm_dirs() -> list[Path]:
    """Directories that may hold WeChat ``kvcomm`` statistic files (uin hints)."""
    roots: list[Path] = []
    if is_windows():
        appdata = os.environ.get("APPDATA", "").strip()
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if appdata:
            roots.append(Path(appdata))
        if local:
            roots.append(Path(local))
        profile = os.environ.get("USERPROFILE", "").strip()
        if profile:
            roots.append(Path(profile) / "AppData" / "Roaming")
    else:
        home = Path.home()
        config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
        if config_home:
            roots.append(Path(config_home).expanduser())
        roots.extend([
            home / ".config",
            home / ".xwechat",
            home / "Library" / "Application Support" / "com.tencent.xinWeChat",
            home / "Library" / "Containers" / "com.tencent.xinWeChat" / "Data"
            / "Library" / "Application Support" / "com.tencent.xinWeChat",
        ])

    relatives = [
        Path("Tencent") / "xwechat" / "net" / "kvcomm",
        Path("Tencent") / "xwechat" / "net_1" / "kvcomm",
        Path("net") / "kvcomm",
        Path("net_1") / "kvcomm",
    ]
    found: list[Path] = []
    for root in roots:
        for rel in relatives:
            found.append(root / rel)
    return _unique_paths(found)


class WeChatDataHit(NamedTuple):
    wxid: str
    base_dir: Path
    account_dir: Path
    session_db: Path | None
    legacy_db: Path | None


def discover_wechat_accounts(extra_bases: list[Path] | None = None) -> list[WeChatDataHit]:
    """Find ``wxid_*`` accounts under custom bases, then the platform defaults."""
    bases: list[Path] = []
    for raw in extra_bases or []:
        path = Path(raw).expanduser()
        if path not in bases:
            bases.append(path)
    for path in default_wechat_data_dirs():
        if path not in bases:
            bases.append(path)

    hits: list[WeChatDataHit] = []
    for base in bases:
        if not base.exists() or not base.is_dir():
            continue
        try:
            accounts = sorted(
                [d for d in base.iterdir() if d.is_dir() and d.name.startswith("wxid_")],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )
        except (OSError, PermissionError):
            continue
        for account in accounts:
            session_db = account / "db_storage" / "session" / "session.db"
            legacy_db = None
            msg_dir = account / "Msg"
            if msg_dir.is_dir():
                try:
                    legacy = sorted(msg_dir.glob("MSG*.db"), key=lambda f: f.stat().st_mtime, reverse=True)
                except OSError:
                    legacy = []
                if legacy:
                    legacy_db = legacy[0]
            if session_db.exists() or legacy_db is not None:
                hits.append(WeChatDataHit(
                    wxid=account.name,
                    base_dir=base,
                    account_dir=account,
                    session_db=session_db if session_db.exists() else None,
                    legacy_db=legacy_db,
                ))
    return hits


def runtime_home(source_root: Path) -> Path:
    """Writable directory for ``.env`` and ``data/``.

    Source checkouts use the repository root on every OS. Frozen Windows
    builds keep using the executable directory. Frozen macOS and Linux
    builds use the per-user data directory so a ``.app`` or AppImage can
    stay read-only. ``WEBOT_APP_HOME`` overrides all of the above.
    """
    explicit = os.getenv("WEBOT_APP_HOME", "").strip()
    if explicit:
        path = Path(explicit).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    if not getattr(sys, "frozen", False):
        return source_root.resolve()

    if is_windows():
        return Path(sys.executable).resolve().parent

    if is_macos():
        path = Path.home() / "Library" / "Application Support" / "wx-assist"
    else:
        data_home = os.getenv("XDG_DATA_HOME", "").strip()
        base = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
        path = base / "wx-assist"
    path.mkdir(parents=True, exist_ok=True)
    os.environ["WEBOT_APP_HOME"] = str(path)
    return path


def try_lock_file(lock_file) -> bool:
    """Non-blocking exclusive lock. Windows uses ``msvcrt``; other OSes use ``flock``."""
    if is_windows():
        import msvcrt

        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl

    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def unlock_file(lock_file) -> None:
    if is_windows():
        import msvcrt

        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def acquire_single_instance(name: str = "wx-assist-17327") -> bool:
    """Return True when this process owns the single-instance lock.

    Windows uses the same named mutex as before (``Global\\\\<name>``).
    Other systems use an exclusive flock in the temp directory. The lock
    is held for the life of the process.
    """
    if is_windows():
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, False, f"Global\\{name}")
        if not handle:
            return True
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(handle)
            return False
        _SINGLE_INSTANCE["mutex"] = handle
        return True

    import fcntl

    path = Path(tempfile.gettempdir()) / f"{name}.lock"
    handle = open(path, "a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False
    _SINGLE_INSTANCE["file"] = handle
    return True


def _escape_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def show_message(title: str, message: str, *, error: bool = False) -> None:
    """Show a native message box, or print when no GUI toolkit is available."""
    if is_windows():
        try:
            import ctypes

            flags = 0x10 if error else 0x40  # MB_ICONERROR / MB_ICONINFORMATION
            ctypes.windll.user32.MessageBoxW(0, message, title, flags)
            return
        except Exception:
            pass
    if is_macos() and shutil.which("osascript"):
        icon = "stop" if error else "note"
        script = (
            f'display dialog "{_escape_applescript(message)}" '
            f'with title "{_escape_applescript(title)}" '
            f'buttons {{"好"}} default button 1 with icon {icon}'
        )
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=120)
            return
        except Exception:
            pass
    if shutil.which("zenity"):
        kind = "--error" if error else "--info"
        try:
            subprocess.run(
                ["zenity", kind, "--title", title, "--text", message],
                check=False,
                timeout=120,
            )
            return
        except Exception:
            pass
    stream = sys.stderr if error else sys.stdout
    print(f"{title}\n{message}", file=stream)


def ask_close_choice() -> str:
    """Ask whether to hide to the tray, quit, or cancel.

    Returns ``tray``, ``quit``, or ``cancel``.
    """
    title = "摘星 · 微信助手"
    message = (
        "关闭窗口后程序仍在后台运行，关键词提醒和定时任务会继续执行。\n\n"
        "「是」最小化到托盘    「否」退出程序    「取消」什么都不做"
    )
    if is_windows():
        try:
            import ctypes

            result = ctypes.windll.user32.MessageBoxW(
                0,
                message,
                title,
                0x3 | 0x20 | 0x40000,  # YESNOCANCEL | ICONQUESTION | TOPMOST
            )
        except Exception:
            return "cancel"
        if result == 6:
            return "tray"
        if result == 7:
            return "quit"
        return "cancel"

    if is_macos() and shutil.which("osascript"):
        script = (
            f'display dialog "{_escape_applescript(message)}" '
            f'with title "{_escape_applescript(title)}" '
            'buttons {"取消", "退出程序", "最小化到托盘"} '
            'default button 3 cancel button 1'
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except Exception:
            return "cancel"
        output = (result.stdout or "") + (result.stderr or "")
        if "最小化到托盘" in output:
            return "tray"
        if "退出程序" in output:
            return "quit"
        return "cancel"

    if shutil.which("zenity"):
        try:
            result = subprocess.run(
                [
                    "zenity", "--list", "--hide-header",
                    "--title", title,
                    "--text", message,
                    "--column", "选择",
                    "最小化到托盘", "退出程序", "取消",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except Exception:
            return "cancel"
        choice = (result.stdout or "").strip()
        if choice == "最小化到托盘":
            return "tray"
        if choice == "退出程序":
            return "quit"
        return "cancel"
    return "cancel"


def schedule_hard_kill(pid: int, delay_sec: int = 5) -> None:
    """Kill ``pid`` after a delay if graceful shutdown stalls.

    On Windows this is ``cmd /c timeout & taskkill``, including source runs.
    On other systems it is ``sleep`` followed by ``kill -9``.
    """
    delay = max(1, int(delay_sec))
    target = int(pid)
    if is_windows():
        subprocess.Popen(
            ["cmd", "/c", f"timeout /t {delay} /nobreak >nul & taskkill /pid {target} /f"],
            creationflags=0x08000000,
            close_fds=True,
        )
        return
    subprocess.Popen(
        ["sh", "-c", f"sleep {delay}; kill -9 {target}"],
        start_new_session=True,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _process_names_for(system: str) -> set[str]:
    if system == "Windows":
        return {"wechat.exe", "weixin.exe"}
    if system == "Darwin":
        custom = os.getenv("MAC_WECHAT_APP_NAME", "WeChat").strip()
        names = {"wechat", "weixin"}
        if custom:
            names.add(custom.lower())
        return names
    return {"wechat", "weixin", "wechat.exe", "weixin.exe"}


def _wechat_via_psutil(system: str) -> tuple[int, str] | None:
    try:
        import psutil
    except ImportError:
        return None
    wanted = _process_names_for(system)
    try:
        processes = psutil.process_iter(["pid", "name"])
    except Exception:
        return None
    for proc in processes:
        try:
            info = proc.info
            name = str(info.get("name") or "")
        except Exception:
            continue
        if name.lower() in wanted:
            pid = info.get("pid")
            if isinstance(pid, int):
                return pid, name
    return None


def _wechat_via_command(system: str) -> tuple[int, str] | None:
    if system == "Windows":
        for image in ("WeChat.exe", "Weixin.exe"):
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {image}", "/NH"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if image.lower() in (result.stdout or "").lower():
                return 0, image
        return None

    names = ["WeChat", "weixin", "wechat"] if system == "Darwin" else ["weixin", "wechat", "WeChat"]
    custom = os.getenv("MAC_WECHAT_APP_NAME", "").strip()
    if system == "Darwin" and custom and custom not in names:
        names.insert(0, custom)
    for name in names:
        try:
            result = subprocess.run(
                ["pgrep", "-x", name],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        first = (result.stdout or "").strip().splitlines()
        if result.returncode == 0 and first and first[0].isdigit():
            return int(first[0]), name
    return None


def wechat_process_report(system_name_override: str | None = None) -> dict:
    """Return whether a WeChat desktop process appears to be running."""
    system = system_name_override or system_name()
    found = _wechat_via_psutil(system)
    if found is None:
        found = _wechat_via_command(system)
    if found is None:
        if system == "Darwin":
            error = "请启动 macOS 微信并授权辅助功能权限"
        elif system == "Windows":
            error = "请登录微信电脑端"
        else:
            error = "未检测到微信进程。Linux 没有官方桌面客户端的密钥提取，可配置 WECHAT_DATA_DIR 与 WCDB_KEY 读取已有数据库"
        return {"ok": False, "value": "微信未运行", "error": error}
    pid, name = found
    if pid:
        value = f"微信运行中 (PID {pid})"
    else:
        value = f"微信运行中 ({name})"
    return {"ok": True, "value": value, "error": None}


def capability_summary() -> dict:
    """What this operating system can do with the current codebase."""
    if is_windows():
        note = "支持从微信进程提取密钥，并通过窗口发送消息。"
    elif is_macos():
        note = "可使用 mac_hybrid / mac_ui 读取和发送。Windows 密钥钩子不可用。"
    else:
        note = (
            "可运行界面、推送、定时任务和 RAG。本地库读取需要自行提供 WCDB_KEY "
            "和 WECHAT_DATA_DIR。不能从微信进程提取密钥，也不能用 Win32 窗口发送。"
        )
    return {
        "system": system_name(),
        "default_backend": default_wechat_backend(),
        "key_hook": supports_key_hook(),
        "window_send": supports_window_send(),
        "mac_accessibility_send": is_macos(),
        "local_db_read": True,
        "in_place_update": supports_in_place_update(),
        "webview_gui": preferred_webview_gui() or "auto",
        "note": note,
    }
