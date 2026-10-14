"""macOS launcher kept for existing commands.

``python desktop.py`` is the cross-platform entry point. This module still
bootstraps the macOS Application Support directory and ``.env.macos`` before
handing off to ``desktop.main``, so older docs and shortcuts keep working.
"""

import os
import platform
import sys
from pathlib import Path


def _app_home() -> Path:
    explicit_home = os.getenv("WEBOT_APP_HOME", "").strip()
    if explicit_home:
        return Path(explicit_home).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path.home() / "Library" / "Application Support" / "wx-assist"
    return Path(__file__).resolve().parent


def ensure_macos_env_file(app_home: Path | None = None) -> Path:
    """Create a macOS-specific env file and point config loading at it."""
    home = app_home or _app_home()
    home.mkdir(parents=True, exist_ok=True)
    env_path = home / ".env.macos"
    if not env_path.exists():
        env_path.write_text(
            "AI_BACKEND=deepseek\n"
            "DEEPSEEK_API_KEY=\n"
            "WECHAT_BACKEND=mac_hybrid\n"
            "MAC_WECHAT_SEND_SHORTCUT=enter\n"
            "BOT_DISPLAY_NAME=群聊小助手\n"
            "WECHAT_GROUPS=*\n"
            "ONBOARDING_DONE=true\n"
            "LOG_LEVEL=INFO\n"
            "LOG_FILE=data/bot.log\n",
            encoding="utf-8",
        )
    os.environ["WEBOT_APP_HOME"] = str(home)
    os.environ.setdefault("WEBOT_ENV_FILE", str(env_path))
    return env_path


def main() -> None:
    if platform.system() != "Darwin":
        print("desktop_mac.py is intended for macOS. Use desktop.py on other systems.")
    ensure_macos_env_file()
    from desktop import main as desktop_main
    desktop_main()


if __name__ == "__main__":
    main()
