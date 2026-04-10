# Cobalt Strike Bridge MCP

> **本项目的灵感来源于** Cobalt Strike 官方的 [Cobalt Strike MCP Server](https://github.com/Cobalt-Strike/cobaltstrike-mcp-server)。  
> 与官方实现不同，本项目通过 **Aggressor Script（`.cna` 插件）** 进行桥接，无需 CS 4.12 引入的 REST API，对更广泛的 CS 版本具有更好的兼容性。

[English → README.md](README.md)

---

## 概述

`Cobalt Strike Bridge MCP` 通过 **Model Context Protocol (MCP)** 为 AI 助手（Claude、Cursor、VS Code Copilot 等）与正在运行的 Cobalt Strike 客户端之间提供自然语言操控接口。

```plaintext
AI 客户端（Claude / Cursor / …）
        │  MCP（stdio / HTTP）
        ▼
  cs_mcp_bridge.py          ← FastMCP 服务端（Python）
        │  HTTP + X-Bridge-Token
        ▼
  cs_bridge.cna（加载于      ← Aggressor Script HTTP 桥接器
  CS 客户端中）                    监听 127.0.0.1:17777
        │  Aggressor API
        ▼
  Cobalt Strike 客户端
```

### 为什么使用 Aggressor Script 而非 REST API？

|          | 官方 CS MCP Server | **本项目**                           |
| -------- | ------------------ | ------------------------------------ |
| 依赖     | CS 4.12+ REST API  | 任何支持 Aggressor Script 的 CS 版本 |
| 连接目标 | 直连 Team Server   | 通过 `.cna` 插件连接 CS **客户端**   |
| 认证方式 | JWT（REST API）    | 共享 Token（`X-Bridge-Token`）       |
| 插件化   | 否                 | **是** — 模块化 `.cna` 文件          |

插件化设计的优势：

- **版本兼容性更好**：Aggressor Script 在远早于 4.12 的版本中就已支持，几乎适配所有在用的 CS 版本
- **无需修改 Team Server 配置**：只需在 CS 客户端加载 `.cna` 文件即可
- **易于扩展**：添加新功能只需在模块中增加处理函数，无需重启 CS

---

## 快速开始

### 前置要求

- **Cobalt Strike 客户端**已运行并连接至 Team Server（任何支持 Aggressor Script 的版本）
- **Python 3.8+**
- `fastmcp >= 2.12.5` 和 `httpx`

### 安装

1. **克隆仓库**

   ```bash
   git clone https://github.com/yourname/Cobalt-Strike-BridgeMCP.git
   cd Cobalt-Strike-BridgeMCP
   ```

2. **创建并激活虚拟环境**（推荐）

   - Windows：

     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```

   - macOS / Linux：

     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. **安装依赖**

   ```bash
   pip install httpx fastmcp
   ```

### 加载 CNA 插件

1. 打开 Cobalt Strike → 菜单栏 **Cobalt Strike** → **Script Manager（脚本管理器）**
2. 点击 **Load**，选择本仓库中的 `cs_bridge.cna`
3. 在 Script Console 中确认如下输出：

   ```plaintext
   [cs-mcp-bridge] Loading CS MCP Bridge...
   [cs-mcp-bridge] Bridge server started on http://127.0.0.1:17777
   [cs-mcp-bridge] Token: cs-mcp-bridge-secret
   ```

> CNA 桥接器默认仅绑定 `127.0.0.1`（本地回环），**不会**对外网暴露。

---

## 配置

### CNA 桥接器配置（`cs_bridge.cna`）

| 变量            | 默认值                 | 说明                                     |
| --------------- | ---------------------- | ---------------------------------------- |
| `$BRIDGE_PORT`  | `17777`                | HTTP 桥接器监听端口                      |
| `$BRIDGE_TOKEN` | `cs-mcp-bridge-secret` | 认证 Token，对应 `X-Bridge-Token` 请求头 |

修改 `cs_bridge.cna` 顶部的全局变量即可更改默认值：

```cna
$BRIDGE_PORT  = 17777;
$BRIDGE_TOKEN = "换成一个强随机字符串";
```

### Python MCP 桥接器配置（`cs_mcp_bridge.py`）

通过**环境变量**传递配置，无需修改源码：

| 环境变量          | 默认值                   | 说明                                 |
| ----------------- | ------------------------ | ------------------------------------ |
| `CS_BRIDGE_URL`   | `http://127.0.0.1:17777` | CNA HTTP 桥接器地址                  |
| `CS_BRIDGE_TOKEN` | `cs-mcp-bridge-secret`   | 必须与 CNA 中的 `$BRIDGE_TOKEN` 一致 |
| `MCP_TRANSPORT`   | `http`                   | MCP 传输协议：`http` 或 `stdio`      |
| `MCP_LISTEN_HOST` | `0.0.0.0`                | HTTP 传输绑定地址                    |
| `MCP_LISTEN_PORT` | `3001`                   | HTTP 传输绑定端口                    |
| `MCP_LISTEN_PATH` | `/mcp`                   | MCP 端点路径                         |

---

## 运行 MCP 服务端

```bash
# HTTP 传输（默认）
python cs_mcp_bridge.py

# stdio 传输（适用于 Claude Desktop 等本地 AI 客户端）
MCP_TRANSPORT=stdio python cs_mcp_bridge.py

# 自定义 Token 和端口
CS_BRIDGE_TOKEN=my-secret MCP_LISTEN_PORT=3001 python cs_mcp_bridge.py
```

---

## Claude Desktop 集成

将以下内容添加到 `claude_desktop_config.json`：

- macOS/Linux：`~/.config/claude-desktop/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "Cobalt Strike Bridge": {
      "command": "C:\\path\\to\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\Cobalt-Strike-BridgeMCP\\cs_mcp_bridge.py"],
      "env": {
        "CS_BRIDGE_URL":   "http://127.0.0.1:17777",
        "CS_BRIDGE_TOKEN": "cs-mcp-bridge-secret",
        "MCP_TRANSPORT":   "stdio"
      }
    }
  }
}
```

macOS/Linux 将 `command` 改为 `/path/to/.venv/bin/python`。

---

## 可用工具（MCP Tools）

### Beacon 管理

| 工具               | 说明                                                   |
| ------------------ | ------------------------------------------------------ |
| `list_beacons`     | 列出所有活跃 Beacon（id、用户、主机、PID、OS、架构等） |
| `get_recent_tasks` | 获取所有 Beacon 最近的任务和输入日志                   |
| `beacon_set_note`  | 为 Beacon 设置备注标签                                 |
| `beacon_remove`    | 从会话列表中移除 Beacon（不终止进程）                  |
| `beacon_sleep`     | 调整 Beacon 回连间隔和抖动                             |

### 命令执行

| 工具                      | 说明                                           |
| ------------------------- | ---------------------------------------------- |
| `beacon_shell`            | 通过 `cmd.exe` 执行 shell 命令                 |
| `beacon_run`              | 直接运行程序（不经过 `cmd.exe`）               |
| `beacon_execute_assembly` | 内存中执行 .NET Assembly（`execute-assembly`） |
| `beacon_inject`           | 将新 Beacon payload 注入指定进程               |

### 文件操作

| 工具              | 说明                           |
| ----------------- | ------------------------------ |
| `beacon_download` | 从目标主机下载文件到 CS 服务器 |
| `beacon_upload`   | 上传本地文件到 Beacon 所在主机 |

### 监听器管理

| 工具              | 说明                   |
| ----------------- | ---------------------- |
| `list_listeners`  | 列出所有已配置的监听器 |
| `create_listener` | 创建新的监听器         |

### 实用工具

| 工具           | 说明                    |
| -------------- | ----------------------- |
| `health_check` | 检查 CNA 桥接器是否在线 |

---

## MCP Resources（实时数据资源）

服务端也通过 **MCP Resources** 暴露实时只读数据：

| 资源 URI                           | 说明                |
| ---------------------------------- | ------------------- |
| `cobalt-strike://beacons/active`   | 当前所有活跃 Beacon |
| `cobalt-strike://listeners/active` | 当前所有活跃监听器  |
| `cobalt-strike://bridge/status`    | CNA 桥接器健康状态  |

---

## 模块化 CNA 架构

Aggressor Script 侧采用模块化结构，便于扩展：

```plaintext
cs_bridge.cna                 ← 主入口：全局配置 + 模块加载 + 启动
modules/
  utils.cna                   ← HTTP 工具函数：响应发送、认证、请求体读取、JSON 解析
  handlers_beacon.cna         ← 所有 /beacon/* 路由处理器
  handlers_listener.cna       ← /listeners 和 /listener/create 处理器
  server.cna                  ← 路由分发（handle_request）+ 服务器启动
```

**新增接口的步骤：**

1. 在 `modules/handlers_*.cna` 中新增 `sub handle_xyz`
2. 在 `modules/server.cna` 的 `handle_request` 路由表中添加对应路径
3. 在 `cs_mcp_bridge.py` 中添加对应的 `@mcp.tool()`

---

## 故障排查

### CNA 桥接器未启动

- 在 CS 的 Script Console 中查看错误信息。
- 确认端口 `17777` 未被占用：`netstat -ano | findstr 17777`（Windows）。

### Python 侧报 `401 Unauthorized`

- 确认 `CS_BRIDGE_TOKEN` 环境变量与 `cs_bridge.cna` 中的 `$BRIDGE_TOKEN` 完全一致。

### Python 侧报 `Connection refused`

- 确认 CNA 脚本已加载且桥接器正在运行（查看 Script Console）。
- 确认 `CS_BRIDGE_URL` 指向正确的地址和端口。

### `ModuleNotFoundError: No module named 'fastmcp'`

- 确认虚拟环境已激活：`.venv\Scripts\activate`（Windows）或 `source .venv/bin/activate`（macOS/Linux）。
- 运行：`pip install httpx fastmcp`。

---

> [!WARNING]
> 本工具提供对 Cobalt Strike 对抗模拟能力的直接访问。  
> **请仅在获得明确书面授权的环境中进行安全测试，切勿用于未授权目标。**
