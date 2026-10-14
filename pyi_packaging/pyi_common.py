"""Shared PyInstaller inputs for Windows, macOS, and Linux.

``build.spec`` (no RAG) and ``build_rag.spec`` (full) both call
:func:`collect`. The specs stay responsible for constructing
``Analysis`` / ``EXE`` / ``BUNDLE``, which only exist while PyInstaller
is executing a spec file.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


_BASE_HIDDEN = [
    "src", "src.bot", "src.config", "src.main", "src.platform_support",
    "src.db", "src.db.schema", "src.db.store",
    "src.assistant", "src.assistant.config", "src.assistant.alert",
    "src.assistant.digest", "src.assistant.scheduler",
    "src.assistant.outbox", "src.assistant.oa_monitor",
    "src.assistant.oa_digest", "src.assistant.oa_groups",
    "src.assistant.oa_parser", "src.assistant.oa_reader",
    "src.assistant.task_center",
    "src.agent", "src.agent.engine", "src.agent.tools",
    "src.agent.registry", "src.agent.mcp_server",
    "src.summarize", "src.summarize.base", "src.summarize.claude_backend",
    "src.summarize.deepseek_backend", "src.summarize.models", "src.summarize.prompts",
    "src.memory", "src.memory.consolidator",
    "src.wechat", "src.wechat.base", "src.wechat.wcdb_backend",
    "src.wechat.wcdb_client", "src.wechat.mac_hybrid_backend",
    "src.wechat.mac_weflow_client",
    "src.wechat.content_codec",
    "src.wechat.mac_ui_backend", "src.wechat.window_controller",
    "src.wechat.keyboard", "src.wechat.helpers", "src.wechat.extract_key",
    "src.wechat.native", "src.wechat.native.injector",
    "src.wechat.image_decrypt", "src.wechat.v2_cache_decrypt",
    "src.wechat.voice_decode", "src.wechat.ilink_push",
    "src.wechat.ilink_receiver",
    "src.wechat.db_crypto", "src.wechat.db_reader",
    "src.web", "src.web.server", "src.web.api_handlers", "src.web.ai_chat",
    "src.web.update",
    "src.nickname", "src.admin",
    "src.utils", "src.utils.logging_config", "src.utils.llm_logger",
    "src.guard", "src.guard.content_filter",
    "src.scheduler", "src.scheduler.cron_scheduler",
    "src.skill", "src.skill.engine",
    "dotenv", "anthropic", "openai", "pydantic",
    "ddgs", "duckduckgo_search",
    "psutil", "pyperclip",
    "webview", "webview.platforms",
    "PIL", "PIL.Image", "PIL.ImageDraw",
    "pystray",
    "requests", "urllib3",
    "APScheduler", "apscheduler.schedulers.background", "apscheduler.triggers.cron",
    "zstandard", "Crypto",
    "src.mcp", "src.mcp.client", "src.mcp.manager",
    "src.mcp.tool_registry", "src.mcp.config_schema",
    "src.im", "src.im.base", "src.im.message", "src.im.delivery",
    "src.im.progress_router", "src.im.push_channel", "src.im.registry",
    "src.im.targets", "src.im.config_schema",
    "src.im.plugins",
    "src.im.plugins.feishu", "src.im.plugins.feishu.adapter",
    "src.im.plugins.feishu.events", "src.im.plugins.feishu.onboarding",
    "src.im.plugins.feishu.openapi_client", "src.im.plugins.feishu.push",
    "src.im.plugins.qqbot", "src.im.plugins.qqbot.adapter",
    "src.im.plugins.qqbot.onboarding", "src.im.plugins.qqbot.openapi_client",
    "src.im.plugins.qqbot.push",
    "src.im.plugins.wechat", "src.im.plugins.wechat.adapter",
    "src.im.plugins.wechat.push",
    "src.assistant.rag_types",
    "src.db.content_cache",
    "src.summarize.errors", "src.summarize.provider_detector",
    "src.summarize.stub_backend",
    "src.wechat.fav_reader", "src.wechat.wcdb_fav_reader",
    "src.wechat.sns_client", "src.wechat.wcdb_sns_reader",
    "src.utils.web_search", "src.utils.op_logger", "src.utils.cron",
    "src.trigger", "src.router",
    "lark_oapi", "lark_oapi.ws", "lark_oapi.event",
]

_RAG_HIDDEN = [
    "src.assistant.rag", "src.assistant.rag.engine",
    "src.assistant.rag.embedder", "src.assistant.rag.vector_store",
    "src.assistant.rag.chunking", "src.assistant.rag.models",
    "src.assistant.rag.reranker",
    "numpy", "chromadb", "fastembed", "onnxruntime",
    "chromadb.telemetry",
    "chromadb.telemetry.product",
    "chromadb.telemetry.product.posthog",
    "chromadb.telemetry.product.events",
    "chromadb.telemetry.opentelemetry",
    "overrides",
    "chromadb_rust_bindings",
    "chromadb.api.rust",
]


def read_app_version(project_root: Path) -> str:
    src = (project_root / "src" / "version.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', src, re.M)
    if not match:
        raise RuntimeError("src/version.py 中找不到 __version__")
    return match.group(1)


def _version_tuple(app_version: str) -> tuple:
    parts = tuple(int(x) for x in app_version.split("."))
    return (parts + (0, 0, 0, 0))[:4]


def write_windows_version_file(project_root: Path, app_version: str, exe_name: str) -> Path:
    """Write the VSVersionInfo file used by Windows executables."""
    ver = _version_tuple(app_version)
    original = f"{exe_name}.exe"
    path = project_root / "build" / "version_info.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "VSVersionInfo(\n"
        "  ffi=FixedFileInfo(\n"
        f"    filevers={ver},\n"
        f"    prodvers={ver},\n"
        "    mask=0x3f,\n"
        "    flags=0x0,\n"
        "    OS=0x40004,\n"
        "    fileType=0x1,\n"
        "    subtype=0x0,\n"
        "    date=(0, 0)\n"
        "  ),\n"
        "  kids=[\n"
        "    StringFileInfo([\n"
        "      StringTable('040904B0', [\n"
        "        StringStruct('CompanyName', 'MaleleStudySpace'),\n"
        "        StringStruct('FileDescription', 'wx-assist'),\n"
        f"        StringStruct('FileVersion', '{app_version}'),\n"
        f"        StringStruct('InternalName', '{exe_name}'),\n"
        "        StringStruct('LegalCopyright', 'MIT License'),\n"
        f"        StringStruct('OriginalFilename', '{original}'),\n"
        "        StringStruct('ProductName', 'wx-assist'),\n"
        f"        StringStruct('ProductVersion', '{app_version}'),\n"
        "      ])\n"
        "    ]),\n"
        "    VarFileInfo([VarStruct('Translation', [1033, 1200])])\n"
        "  ]\n"
        ")\n",
        encoding="utf-8",
    )
    return path


def _find_webview_dir() -> Path | None:
    import site

    candidates = []
    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        user_sp = site.getusersitepackages()
    except Exception:
        user_sp = None
    if user_sp:
        candidates.append(user_sp)
    for sp in candidates:
        lib = Path(sp) / "webview" / "lib"
        if lib.exists():
            return lib
    return None


def windows_webview_binaries() -> list[tuple[str, str]]:
    """WebView2 loader DLLs. Required on Windows, omitted elsewhere."""
    webview_dir = _find_webview_dir()
    if webview_dir is None:
        raise FileNotFoundError(
            "webview package not found. Install with: pip install pywebview"
        )
    runtime = webview_dir / "runtimes" / "win-x64" / "native" / "WebView2Loader.dll"
    interop = webview_dir / "WebBrowserInterop.x64.dll"
    if not runtime.exists():
        raise FileNotFoundError(f"WebView2Loader.dll not found at {runtime}")
    if not interop.exists():
        raise FileNotFoundError(f"WebBrowserInterop.x64.dll not found at {interop}")
    return [
        (str(runtime), "./runtimes/win-x64/native"),
        (str(interop), "./lib"),
    ]


def platform_hiddenimports(system: str) -> list[str]:
    if system == "Windows":
        return [
            "uiautomation",
            "win32api", "win32gui", "win32con", "win32clipboard", "win32process",
            "webview.platforms.edgechromium",
            "pystray._win32",
        ]
    if system == "Darwin":
        return [
            "webview.platforms.cocoa",
            "pystray._darwin",
        ]
    return [
        "webview.platforms.gtk",
        "webview.platforms.qt",
        "pystray._gtk",
        "pystray._xorg",
        "pystray._appindicator",
    ]


def hiddenimports(*, with_rag: bool, system: str) -> list[str]:
    items = list(_BASE_HIDDEN)
    items.extend(platform_hiddenimports(system))
    if with_rag:
        items.extend(_RAG_HIDDEN)
    return items


def excludes(*, with_rag: bool) -> list[str]:
    names = ["tkinter", "matplotlib", "scipy", "jedi", "IPython"]
    if not with_rag:
        names.extend(["numpy", "chromadb", "fastembed", "onnxruntime"])
    return names


def binaries(project_root: Path, *, system: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if system == "Windows":
        found.extend(windows_webview_binaries())
        key_dll = project_root / "lib" / "wx_key.dll"
        if key_dll.exists():
            found.append((str(key_dll), "lib"))
        else:
            print(
                "warning: lib/wx_key.dll not found; the Windows key hook will "
                "not be bundled. Place the DLL in lib/ before a release build.",
                file=sys.stderr,
            )
    return found


def datas(project_root: Path, *, with_rag: bool) -> list[tuple[str, str]]:
    ui_dist = project_root / "ui" / "dist"
    if not ui_dist.exists():
        raise FileNotFoundError(
            "ui/dist is missing. Build the frontend first: "
            "cd ui && npm install && npm run build"
        )
    items = [
        ("ui/dist", "ui/dist"),
        (".env.example", "."),
        ("favicon.ico", "."),
    ]
    wasm = project_root / "lib" / "wasm"
    if wasm.exists():
        items.append(("lib/wasm", "lib/wasm"))
    if with_rag:
        models = project_root / "models"
        if models.exists():
            items.append((str(models), "models"))
        else:
            print(
                "warning: models/ is missing; the full build will not embed "
                "the local embedding model.",
                file=sys.stderr,
            )
    return items


def collect(specpath, *, with_rag: bool, exe_name: str, system: str | None = None) -> dict:
    """Return kwargs for Analysis, EXE, and an optional macOS BUNDLE.

    ``system`` defaults to the machine running the build. Tests pass an
    explicit name so the plan can be checked without PyInstaller.
    """
    project_root = Path(specpath)
    host = system or ("Windows" if sys.platform == "win32" else "Darwin" if sys.platform == "darwin" else "Linux")
    app_version = read_app_version(project_root)
    version_file = None
    if host == "Windows":
        version_file = write_windows_version_file(project_root, app_version, exe_name)

    icon = None
    if host == "Windows":
        ico = project_root / "favicon.ico"
        if ico.exists():
            icon = str(ico)
    elif host == "Linux":
        png = project_root / "ui" / "public" / "favicon.png"
        if png.exists():
            icon = str(png)

    analysis = {
        "scripts": ["desktop.py"],
        "pathex": [str(project_root)],
        "binaries": binaries(project_root, system=host),
        "datas": datas(project_root, with_rag=with_rag),
        "hiddenimports": hiddenimports(with_rag=with_rag, system=host),
        "hookspath": [],
        "hooksconfig": {},
        "runtime_hooks": [],
        "excludes": excludes(with_rag=with_rag),
        "win_no_prefer_redirects": False,
        "win_private_assemblies": False,
        "cipher": None,
        "noarchive": False,
    }

    exe = {
        "name": exe_name,
        "debug": False,
        "bootloader_ignore_signals": False,
        "strip": bool(with_rag),
        "upx": True,
        "upx_exclude": [],
        "runtime_tmpdir": None,
        "console": False,
        "disable_windowed_traceback": False,
        "argv_emulation": False,
        "target_arch": None,
        "codesign_identity": None,
        "entitlements_file": None,
    }
    if icon:
        exe["icon"] = icon
    if version_file is not None:
        exe["version"] = str(version_file)

    bundle = None
    if host == "Darwin":
        bundle = {
            "name": f"{exe_name}.app",
            "icon": None,
            "bundle_identifier": "space.malele.wx-assist",
            "info_plist": {
                "CFBundleName": "wx-assist",
                "CFBundleDisplayName": "摘星",
                "CFBundleShortVersionString": app_version,
                "CFBundleVersion": app_version,
                "NSHighResolutionCapable": True,
            },
        }
    return {
        "system": host,
        "version": app_version,
        "analysis": analysis,
        "exe": exe,
        "bundle": bundle,
    }
