# 手动获取连接凭证（WCDB_KEY）

macOS / Linux **不能**从本机微信进程自动提取密钥（该能力依赖 Windows 的 `wx_key.dll`）。
需要先在 **Windows**（实体机或本机虚拟机，见 §2.1）上用本应用完成自动提取，再把密钥填到其它系统的「手动配置」里。

本文只说明本应用已经支持的流程，不介绍任何逆向、注入或第三方抓钥工具。

## 1. 连接凭证是什么

| 字段 | 说明 |
|------|------|
| **连接凭证 / `WCDB_KEY`** | 64 位十六进制字符串（仅 `0-9`、`a-f` / `A-F`），用于解密本地微信数据库 |
| **微信数据目录 / `WECHAT_DATA_DIR`** | 包含 `wxid_*` 账号文件夹的**父目录** |
| **账号 ID / `WXID`** | 形如 `wxid_…` 的账号目录名 |
| **数据库路径 / `DB_PATH`** | 通常为 `…/wxid_…/db_storage/session/session.db` |

密钥必须与你要读取的那份数据（同一账号的数据目录）匹配。推荐做法：在 Windows 上自动提取后，把密钥复制到 macOS / Linux，并指向**同一账号**的数据目录（本机目录，或从 Windows 拷贝过来的目录）。

## 2. 在 Windows 上自动获取（推荐）

1. 安装并登录 **微信电脑版**，保持登录状态。
2. 在同一台 Windows 电脑上运行摘星（安装包或源码 `python desktop.py`）。
3. 首次启动进入引导页「环境准备与连接」→ 点击 **自动连接 / 自动提取密钥**。
4. 按界面提示操作（必要时按提示退出并重新登录微信）。成功后应用会把 `WCDB_KEY` 等写入本地配置。
5. 之后可在应用内查看密钥：
   - 打开 **系统配置 → 连接凭证**
   - 点击眼睛图标显示 **WCDB 密钥**，复制全部 64 位字符
6. 也可在运行目录的 `.env` 文件中查看 `WCDB_KEY=` 这一行（请勿把该文件提交到 Git 或发给他人）。

Windows 打包若要自带自动提取，需在仓库 `lib/` 下放好 `wx_key.dll` 再打包；详见 [build.md](build.md)。

## 2.1 只有 Mac、没有 Windows 电脑时（推荐：本机 Windows 虚拟机）

本应用**不会**在 macOS 上从微信进程抓取密钥（不做内存扫描、注入或关闭 SIP）。
若你只有一台 Mac，请用虚拟机跑 Windows，走与实体 Windows 相同的「自动连接」：

1. 安装免费虚拟机（例如 [UTM](https://mac.getutm.app/)）或 Parallels / VMware，创建并安装 Windows 11。
2. 在虚拟机里安装 **微信 Windows 版**，用**同一微信账号**登录（可扫码）。
3. 在虚拟机里运行摘星（Windows 安装包，或把本仓库拷进虚拟机后 `python desktop.py`）。
4. 引导页点 **自动连接**，拿到 64 位 `WCDB_KEY`。
5. 把密钥复制到 Mac 端摘星的「手动配置」；`WECHAT_DATA_DIR` / `WXID` 填 **Mac 本机**已有的数据目录（不必从虚拟机拷库，只要是同一账号）。

说明：密钥与账号绑定；Windows 虚拟机里自动提取的密钥，可用于解密 Mac 上同一账号的本地库。Mac 端默认后端 `mac_hybrid` 在配置了 `WCDB_KEY` 后会走纯 Python 读取，并仍用辅助功能发消息。

不推荐、也不在文档中提供：关闭 SIP、重签名微信、使用第三方内存扫描工具获取密钥。

## 3. 在 macOS / Linux 上手动填写

### 引导页「手动配置」

1. 打开摘星，进入「环境准备与连接」。
2. 若提示「当前系统不支持自动提取密钥」，点 **前往手动配置**（或右上角「无法获取？手动配置」）。
3. 粘贴 64 位连接凭证。
4. 填写 `wxid` 与数据库路径（或先只填密钥，下一步再选数据目录）。
5. 点 **保存并下一步**。

### 系统配置里补填 / 修改

**系统配置 → 连接凭证** 可随时编辑 `WCDB 密钥`、`wxid`、数据库路径；改完后需重启助手服务。

### 数据目录常见位置

`WECHAT_DATA_DIR` 应指向包含 `wxid_*` 文件夹的父目录（不是 `wxid_*` 本身）。

**macOS 常见路径（按本机实际存在的为准）：**

- `~/Documents/xwechat_files`
- `~/Documents/WeChat Files`
- `~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files`
- `~/Library/Containers/com.tencent.xinWeChat/Data/Documents/WeChat Files`

也可在微信里查看：设置 → 账号与存储 → 存储位置 / 数据目录，再取其上一级（含多个 `wxid_*` 时）或该目录的父目录。

**Windows 常见路径：**

- `文档\xwechat_files`
- `文档\WeChat Files`

**Linux：** 本机通常没有官方微信客户端的密钥钩子。把 Windows 上同一账号的数据目录拷过来，设置 `WECHAT_DATA_DIR` 并填写对应的 `WCDB_KEY` 即可走纯 Python 读取路径（见根目录 README「技术说明」）。

## macOS 推荐配置（可直接照填）

在 Finder 按 `Cmd+Shift+G` 粘贴路径即可打开。

### 常见数据目录（按优先级）

| 优先级 | 路径 |
|--------|------|
| 1（多数新版微信） | `~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files` |
| 2 | `~/Documents/xwechat_files` |
| 3 | `~/Documents/WeChat Files` |
| 4 | `~/Library/Containers/com.tencent.xinWeChat/Data/Documents/WeChat Files` |

`WECHAT_DATA_DIR` 填**含账号文件夹的父目录**（能看到 `wxid_*` 的那一层），不要填到某个 `wxid_*` 里面。

打开数据目录后，账号文件夹名即 `WXID`（完整名称，含末尾哈希后缀，如 `wxid_xxxx_2b41`）。  
`DB_PATH` 一般为：

`…/<WXID>/db_storage/session/session.db`

注意：自动扫描只认以 `wxid_` 开头的文件夹；若账号目录是 `qq数字_xxxx` 这类，请在手动配置里显式填写 `WXID` 与 `DB_PATH`。

### 引导页 / 环境变量对照

| 界面字段 | 环境变量 | 示例 |
|----------|----------|------|
| 连接凭证 | `WCDB_KEY` | 64 位十六进制（从 Windows 自动提取后粘贴） |
| 微信数据目录 | `WECHAT_DATA_DIR` | `~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files` |
| 账号 ID | `WXID` | `wxid_xxxxxxxx_xxxx`（完整文件夹名） |
| 数据库路径 | `DB_PATH` | `$WECHAT_DATA_DIR/$WXID/db_storage/session/session.db` |
| 后端 | `WECHAT_BACKEND` | `mac_hybrid`（macOS 默认；有 `WCDB_KEY` 时自动用纯 Python 读取） |

### `.env` / `.env.macos` 模板

打包后的 `.app` 可写配置目录：

`~/Library/Application Support/wx-assist/`

（源码运行则在仓库根目录；`desktop_mac.py` 会准备 `.env.macos`。）

```bash
# === WeChat（macOS 手动配置）===
WECHAT_BACKEND=mac_hybrid
WECHAT_DATA_DIR=/Users/你的用户名/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files
WXID=wxid_xxxxxxxx_xxxx
DB_PATH=/Users/你的用户名/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_xxxxxxxx_xxxx/db_storage/session/session.db
WCDB_KEY=请粘贴64位十六进制密钥

WECHAT_GROUPS=*
```

也可用 `WEBOT_APP_HOME` 覆盖应用数据目录。应用日志一般在：

`~/Library/Application Support/wx-assist/data/bot.log`

macOS **不能**自动提取密钥；请用 Windows 实体机或本机 Windows 虚拟机（§2.1）自动获取后粘贴。


## 4. 校验要点

- 密钥长度必须是 **恰好 64** 位十六进制；多空格、少一位都会失败。
- `wxid` 一般与数据目录下的文件夹名一致。
- 数据库文件优先选 `db_storage/session/session.db`。
- 填好后可在「系统配置 → 连接凭证」使用测试/校验（若界面提供），或重启助手后看会话列表是否能加载。

## 5. 安全提醒

- `WCDB_KEY` 能解密你的本地聊天数据，请只保存在本机配置中，不要发到群聊、邮件或公开仓库。
- 不要把 `.env` / `.env.macos` 提交到 Git。
- 本项目不提供、也不支持通过逆向工程或第三方工具获取密钥的说明。

## 相关文档

- [上手指南](getting-started.md)
- [打包说明](build.md)
- 根目录 [README](../README.md) 的「技术说明」平台能力表
