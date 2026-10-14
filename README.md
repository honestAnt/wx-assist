<div align="center">

# 摘星 · 微信助手

从海量消息里，摘出最值得关注的。

**关键词提醒 · AI 群摘要 · 多平台推送 · 公众号速读 · 公众号实时提醒 · 手机扫码访问 · 收藏整理 · AI 对话 · 朋友圈归档 · 聊天导出 · RAG 语义检索 · AI Agent 智能助手 · MCP 工具扩展**

[在线体验](https://wx-assist-demo.onrender.com) · [技术文档](doc/) · [下载](https://github.com/MaleleStudySpace/wx-assist/releases)

</div>

---

群里有人问"今晚聚餐去哪吃"，你看到时已经散场了。
收藏了 500 条内容，想找那条"上次记的笔记在哪"，翻了 20 分钟也翻不到。
关注了一堆公众号，每天的推送翻都翻不完，越积越多——最后索性不看了。

微信不会提醒你，不会帮你整理，不会帮你导出。
它只会让红点越来越多，让收藏越来越深，让重要消息越来越远。

---

> **版本说明**  
> 当前完整版包含 RAG 语义检索所需全部依赖（ChromaDB + ONNX Runtime + 嵌入模型），程序体积约 **250 MB**，每次启动需进行数据索引（约 1-5 分钟，取决于数据量）。  
> 另提供 **精简版（no-rag）**——去除了 RAG 本地部署（语义检索不可用），其他功能不受影响，体积约 **90 MB**，首次启动无需索引，适合不需要语义搜索的用户。  

---

## 功能

- **关键词提醒** — 在指定群聊设置关注词，命中后即时推送到已绑定的平台
- **多平台消息推送** — 支持绑定微信、QQ 机器人与飞书，扫码即用；摘要、提醒等推送可自由选择投递渠道
- **群聊 AI 摘要** — 多个群聊打包成一个分组，定时生成一份合并摘要（按群分段），消息量大时自动降级，AI 标注待办与决定
- **公众号助手** — 按主题分组，AI 定时汇总文章生成摘要；
- **公众号实时提醒** — 关注的公众号发布新文章时，即时推送 AI 速读摘要到微信
- **手机扫码访问** — 同一局域网下，手机扫描二维码即可访问 Web 控制台
- **聊天导出** — 打包聊天记录为离线 HTML/Json 档案，含文字、图片、语音、视频
- **收藏整理** — 浏览、搜索、筛选收藏内容，AI 对话查询，一键导出
- **朋友圈归档** — 导出为离线 HTML，图片视频完整保留，AI 回顾动态
- **AI 对话** — 基于聊天记录 / 收藏 / 朋友圈 / 公众号的上下文对话，支持 RAG 语义检索精准召回
- **AI Agent 智能助手** — 扫码绑定微信、QQ、飞书 与 Agent 对话，调用 20+ 工具完成状态查询、消息搜索、配置管理、摘要生成等操作，ReAct 推理循环自动拆解复杂指令
- **RAG 语义检索** — 对公众号文章、朋友圈、收藏内容自动建立语义索引，AI 对话与 Agent 检索时精准召回最相关内容，不再依赖关键词"猜"
- **MCP 工具 和 SKILL 扩展** — 通过 MCP 协议和 自定义SKILL 给 Agent 装上"超能力" --即插即用，持续扩展,让摘星Agent获取联网搜索、文件读写等能力，更多功能等你发现。
- **定时任务** — 定时执行预设的任务，为 Agent 设计时间表，到点自动执行。

## 在线体验

> **零安装，零配置，打开即用。**

👉 [点击进入 Demo](https://wx-assist-demo.onrender.com)

Demo 使用模拟数据，AI 功能真实调用。响应式设计，手机也能用。

## 截图
<div align="center">

#### 绑定微信

![绑定微信](doc/screenshots/ilink.png)

#### Agent对话

![Agent对话](doc/screenshots/Agent.png)

#### 会话管理

![会话管理](doc/screenshots/chat.png)

#### 收藏助手

![收藏助手](doc/screenshots/fav.png)

#### 朋友圈归档

![朋友圈归档](doc/screenshots/sns.png)

#### 公众号助手

![公众号助手](doc/screenshots/oa.png)

#### MCP工具扩展

![公众号助手](doc/screenshots/mcptab.png)

</div>

## 模块架构

```
┌──────────────────────────────────────────────────────────────┐
│                         Web UI                               │
│  运行状态 · 群聊助手 · 会话管理 · 收藏助手 · 朋友圈 · 公众号     │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                      功能模块                                 │
│  关键词提醒  群聊AI摘要  公众号速读  公众号即时提醒              │
│  收藏整理    朋友圈归档  聊天导出    AI对话                     │
│  AI Agent 智能助手    RAG 语义检索   MCP 工具扩展               │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                      核心服务                                 │
│  消息路由 · 定时调度 · AI后端 · 群记忆 · 通知队列 · 多平台推送   │
│  Agent 引擎 · MCP Server                                      │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                      数据层                                   │
│  微信本地数据库 · 本地存储 (SQLite) · 语义向量库 (ChromaDB)     │
└──────────────────────────────────────────────────────────────┘
                              │
                         ┌────┴────┐
                         │ 推送平台 │ ← 微信 / QQ / 飞书
                         └─────────┘
```

## 技术说明

Windows、macOS、Linux 都可以从源码运行界面、推送、定时任务和（可选的）RAG。核心数据处理在本机完成，不使用 AI 功能时聊天记录、收藏、朋友圈等数据不会离开本机。使用 AI 功能时，相关上下文会按用户配置发送至对应的第三方 AI API。

和微信桌面客户端相关的能力仍然分平台：

| 能力 | Windows | macOS | Linux |
|------|:-------:|:-----:|:-----:|
| 界面、飞书/QQ 推送、定时任务、Agent | 是 | 是 | 是 |
| 本地数据库读取（已有 `WCDB_KEY` + 数据目录） | 是 | 是 | 是 |
| 从微信进程自动提取密钥 | 是 | 否 | 否 |
| 通过窗口自动化发送消息 | 是 | 是（辅助功能） | 否 |
| 打包产物 | `.exe` | `.app` | 二进制，可选 AppImage |
| 安装包自动替换更新 | 是 | 否 | 否 |

Linux 没有官方微信客户端的密钥钩子。把 Windows 上已经解密或已经导出的数据目录指到 `WECHAT_DATA_DIR`，并填写 `WCDB_KEY` 后，纯 Python 读取路径可以工作。不能从本机微信进程里抓密钥，也不能用 Win32 窗口发送。

语义检索（RAG）基于 ChromaDB + fastembed，100% 本地运行。模型文件随完整包分发，无需联网下载，不依赖任何云端服务。

详细架构见 [doc/](doc/) 目录，打包步骤见 [doc/build.md](doc/build.md)。

技术栈：Python 3.13 · React 19 · Tailwind 4 · ChromaDB · fastembed · PyInstaller

## 快速开始

**下载**

从 [Releases](https://github.com/MaleleStudySpace/wx-assist/releases) 下载对应系统的文件：

| 版本 | Windows | macOS | Linux | 说明 |
|------|---------|-------|-------|------|
| 完整版 | `wx-assist.exe` | `wx-assist.app` | `wx-assist` | 含语义检索，首次启动需索引数据 |
| 精简版 | `wx-assist_no_rag.exe` | `wx-assist_no_rag.app` | `wx-assist_no_rag` | 去掉语义检索，其余功能不变 |

Windows 双击 `.exe`。macOS 打开 `.app`（首次可能需要在「隐私与安全性」里放行，并给微信辅助功能权限）。Linux 给二进制加上可执行权限后运行：`chmod +x wx-assist && ./wx-assist`。首次启动进入引导流程。

**从源码启动**

需要 Python 3.13+、Node.js 18+。微信电脑版只在要读取本机数据时才需要。

```bash
pip install -r requirements.txt
cd ui && npm install && npm run build && cd ..
python desktop.py
```

Windows 也可以用 `start.bat`。macOS / Linux 可以用 `./start.sh`。已有的 `python desktop_mac.py` 仍会准备 macOS 的 `.env.macos` 再进入同一个桌面入口。

Linux 若要原生窗口而不是浏览器，需要系统里的 GTK / WebKit，例如 Debian/Ubuntu：

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

没有这套库时，程序会自动改用系统浏览器打开 `http://127.0.0.1:17327`。

语义检索是可选依赖。装上之后源码模式会自动启用，没装则只是语义搜索不可用：

```bash
pip install -r requirements-rag.txt
```

**本地打包**

在对应系统上执行（PyInstaller 不能交叉编译）：

```bash
pip install pyinstaller
python scripts/build.py            # 精简版
python scripts/build.py --rag      # 完整版
python scripts/build.py --both
```

也可以直接用 spec：

```bash
pyinstaller build.spec --noconfirm
pyinstaller build_rag.spec --noconfirm
```

产物：

| 系统 | 精简版 | 完整版 |
|------|--------|--------|
| Windows | `dist/wx-assist_no_rag.exe` | `dist/wx-assist.exe` |
| macOS | `dist/wx-assist_no_rag.app` | `dist/wx-assist.app` |
| Linux | `dist/wx-assist_no_rag` | `dist/wx-assist` |

Linux 还可以在装有 `appimagetool` 时执行 `./scripts/package_appimage.sh`（加 `--rag` 打完整版），额外得到 AppImage。没有该工具时脚本只留下上面的二进制。

Windows 密钥提取仍需要把 `lib/wx_key.dll` 放在仓库的 `lib/` 里再打包，否则安装包里不会带这个钩子。数据库读取本身不依赖该 DLL。

## 致谢

本项目在 AI 辅助编程下完成，底层实现参考了多个优秀开源项目。在此对以下前辈及开源贡献者表示最诚挚的感谢：

- **[LifeArchiveProject/WeChatDataAnalysis](https://github.com/LifeArchiveProject/WeChatDataAnalysis)** · **[cancelGuMu/webot](https://github.com/cancelGuMu/webot)** · **[hicccc77/WeFlow](https://github.com/hicccc77/WeFlow)** · **[jackwener/wx-cli](https://github.com/jackwener/wx-cli)** · **[ylytdeng/wechat-decrypt](https://github.com/ylytdeng/wechat-decrypt)** — 为本项目的框架和底层实现提供了思路和指导。

正是你们，让我的想法得以实现，让这一切成为可能，再次感谢。

如果有好的建议或发现了问题，欢迎提交 Issue 或 PR。

## 免责声明

1. 本项目主要面向个人本地使用。核心数据处理在本机完成；使用 AI 功能时，相关上下文会按用户配置发送至对应的第三方 AI API。请自行做好数据备份。
2. 仅供个人学习与本地使用。使用者应遵守相关法律法规及微信用户协议。
3. 按"现状"提供，不提供任何明示或暗示的保证。

   > **安全提示：** 部分杀软可能将编译后的可执行文件误报为威胁，此属 PyInstaller 打包工具的常见现象，请以排除项方式信任使用。

4. AI 功能依赖第三方 API 服务（如 DeepSeek / Claude），请遵守对应服务商协议。
