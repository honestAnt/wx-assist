# 打包

在目标操作系统上打包。PyInstaller 不能从 Linux 交叉编译出 Windows `.exe` 或 macOS `.app`。

## 准备

```bash
pip install -r requirements.txt
pip install pyinstaller
# 完整版再装：
pip install -r requirements-rag.txt
cd ui && npm install && npm run build && cd ..
```

`ui/dist` 必须存在，spec 会把它打进包里。

## 命令

```bash
python scripts/build.py            # 精简版，对应 build.spec
python scripts/build.py --rag      # 完整版，对应 build_rag.spec
python scripts/build.py --both
```

等价的底层命令：

```bash
pyinstaller build.spec --noconfirm
pyinstaller build_rag.spec --noconfirm
```

两个 spec 共用 `packaging/pyi_common.py`。它按当前系统选择：

- Windows：打入 WebView2 运行库；若存在 `lib/wx_key.dll` 则一并打入；写入 exe 版本资源。
- macOS：生成 `.app`（Cocoa WebView）。不打 Windows DLL。
- Linux：生成单个可执行文件，图标用 `ui/public/favicon.png`。窗口后端由 pywebview 在 GTK / Qt 里选择。

精简版排除 `numpy`、`chromadb`、`fastembed`、`onnxruntime`。完整版会带上这些模块；如果仓库里有 `models/`，也会打进包里。

## 产物放在哪

| 系统 | 精简版 | 完整版 | 运行时数据 |
|------|--------|--------|------------|
| Windows | `dist/wx-assist_no_rag.exe` | `dist/wx-assist.exe` | exe 同目录（与以前相同） |
| macOS | `dist/wx-assist_no_rag.app` | `dist/wx-assist.app` | `~/Library/Application Support/wx-assist` |
| Linux | `dist/wx-assist_no_rag` | `dist/wx-assist` | `$XDG_DATA_HOME/wx-assist` 或 `~/.local/share/wx-assist` |

源码运行时，三个系统都把 `.env` 和 `data/` 放在仓库根目录。`WEBOT_APP_HOME` 可以改这个位置。

## Linux AppImage

```bash
./scripts/package_appimage.sh          # 精简版
./scripts/package_appimage.sh --rag    # 完整版
```

脚本先调用 `scripts/build.py`。机器上有 `appimagetool` 时，再在 `dist/` 下生成 AppImage。没有该工具时，二进制本身就是可用产物。

## 仍然只在 Windows 上的部分

- `lib/wx_key.dll` 密钥钩子，以及 `src/wechat/native/injector.py` 里的注入回退。
- Win32 窗口发送（`window_controller` / `keyboard`）。
- 安装包的就地替换更新（`src/web/update.py` 的 bat 助手）。其它系统提示手动替换下载的文件。

macOS 发送走 `mac_hybrid` / `mac_ui`，需要辅助功能权限，并且读取加密库时依赖本机的 WeFlow `libWCDB.dylib`（见 `src/wechat/mac_weflow_client.py`）。仓库不附带这个库。
