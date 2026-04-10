# Cobalt Strike Bridge MCP

> **Inspired by** the official [Cobalt Strike MCP Server](https://github.com/Cobalt-Strike/cobaltstrike-mcp-server) by the Cobalt Strike team.  
> This project takes a different approach: instead of requiring the CS REST API (introduced in CS 4.12), it bridges through **Aggressor Script (`.cna` plugin)**, which gives broader version compatibility with any CS client that supports Aggressor.

[中文文档 → README.zh-CN.md](README.zh-CN.md)

---

## Overview

`Cobalt Strike Bridge MCP` provides a natural-language interface between AI assistants (Claude, Cursor, VS Code Copilot, etc.) and a running Cobalt Strike client, using the **Model Context Protocol (MCP)**.

```plaintext
AI Client (Claude / Cursor / …)
        │  MCP (stdio / HTTP)
        ▼
  cs_mcp_bridge.py          ← FastMCP server (Python)
        │  HTTP + X-Bridge-Token
        ▼
  cs_bridge.cna (loaded     ← Aggressor Script HTTP bridge
  inside CS client)               running on 127.0.0.1:17777
        │  Aggressor API
        ▼
  Cobalt Strike Client
```

### Why Aggressor Script instead of the REST API?

|              | Official CS MCP Server | **This project**                      |
| ------------ | ---------------------- | ------------------------------------- |
| Requires     | CS 4.12+ REST API      | Any CS version with Aggressor support |
| Connects to  | Team server directly   | CS **client** (via loaded `.cna`)     |
| Auth model   | JWT via REST API       | Shared token (`X-Bridge-Token`)       |
| Plugin-based | No                     | **Yes** — modular `.cna` files        |

---

## Getting Started

### Prerequisites

- **Cobalt Strike client** running and connected to a team server (any version supporting Aggressor Script)
- **Python 3.8+**
- `fastmcp >= 2.12.5` and `httpx`

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourname/Cobalt-Strike-BridgeMCP.git
   cd Cobalt-Strike-BridgeMCP
   ```

2. **Create and activate a virtual environment** (recommended)

   - Windows:

     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```

   - macOS / Linux:

     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**

   ```bash
   pip install httpx fastmcp
   ```

### Loading the CNA Plugin

1. Open Cobalt Strike → **Cobalt Strike** menu → **Script Manager**
2. Click **Load** and select `cs_bridge.cna` from this repository
3. Verify in the Script Console:

   ```plaintext
   [cs-mcp-bridge] Loading CS MCP Bridge...
   [cs-mcp-bridge] Bridge server started on http://127.0.0.1:17777
   [cs-mcp-bridge] Token: cs-mcp-bridge-secret
   ```

> The CNA bridge binds only to `127.0.0.1` (loopback). It is **not** exposed to the network by default.

---

## Configuration

All runtime settings are passed via **environment variables** or directly in `cs_bridge.cna`.

### CNA Bridge settings (`cs_bridge.cna`)

| Variable        | Default                | Description                               |
| --------------- | ---------------------- | ----------------------------------------- |
| `$BRIDGE_PORT`  | `17777`                | Port the HTTP bridge listens on           |
| `$BRIDGE_TOKEN` | `cs-mcp-bridge-secret` | Shared secret for `X-Bridge-Token` header |

Edit the top of `cs_bridge.cna` to change defaults:

```cna
$BRIDGE_PORT  = 17777;
$BRIDGE_TOKEN = "change-me-to-something-strong";
```

### Python MCP Bridge settings (`cs_mcp_bridge.py`)

| Environment Variable | Default                  | Description                           |
| -------------------- | ------------------------ | ------------------------------------- |
| `CS_BRIDGE_URL`      | `http://127.0.0.1:17777` | URL of the CNA HTTP bridge            |
| `CS_BRIDGE_TOKEN`    | `cs-mcp-bridge-secret`   | Must match `$BRIDGE_TOKEN` in the CNA |
| `MCP_TRANSPORT`      | `http`                   | MCP transport: `http` or `stdio`      |
| `MCP_LISTEN_HOST`    | `0.0.0.0`                | Bind host for HTTP transport          |
| `MCP_LISTEN_PORT`    | `3001`                   | Bind port for HTTP transport          |
| `MCP_LISTEN_PATH`    | `/mcp`                   | URL path for the MCP endpoint         |

---

## Running the MCP Server

```bash
# HTTP transport (default)
python cs_mcp_bridge.py

# stdio transport (for Claude Desktop / local AI clients)
MCP_TRANSPORT=stdio python cs_mcp_bridge.py

# Custom token + port
CS_BRIDGE_TOKEN=my-secret MCP_LISTEN_PORT=3001 python cs_mcp_bridge.py
```

---

## Claude Desktop Integration

Add to `claude_desktop_config.json` (`~/.config/claude-desktop/` on macOS/Linux, `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "Cobalt Strike Bridge": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/Cobalt-Strike-BridgeMCP/cs_mcp_bridge.py"],
      "env": {
        "CS_BRIDGE_URL":   "http://127.0.0.1:17777",
        "CS_BRIDGE_TOKEN": "cs-mcp-bridge-secret",
        "MCP_TRANSPORT":   "stdio"
      }
    }
  }
}
```

On Windows, use the full path to `.venv\Scripts\python.exe`.

---

## Available Tools

### Beacon Management

| Tool               | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| `list_beacons`     | List all active beacons (id, user, host, pid, os, arch, …) |
| `get_recent_tasks` | Retrieve recent task / input logs for all beacons          |
| `beacon_set_note`  | Annotate a beacon with a custom note                       |
| `beacon_remove`    | Remove a beacon from the session list                      |
| `beacon_sleep`     | Change beacon sleep interval and jitter                    |

### Command Execution

| Tool                      | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `beacon_shell`            | Run a command via `cmd.exe` on a beacon                |
| `beacon_run`              | Run a program directly (no `cmd.exe` wrapper)          |
| `beacon_execute_assembly` | In-memory .NET assembly execution (`execute-assembly`) |
| `beacon_inject`           | Inject a new beacon payload into a target process      |

### File Operations

| Tool              | Description                                           |
| ----------------- | ----------------------------------------------------- |
| `beacon_download` | Download a file from the target host to the CS server |
| `beacon_upload`   | Upload a local file to the beacon host                |

### Listener Management

| Tool              | Description               |
| ----------------- | ------------------------- |
| `list_listeners`  | List configured listeners |
| `create_listener` | Create a new listener     |

### Utility

| Tool           | Description                       |
| -------------- | --------------------------------- |
| `health_check` | Check if the CNA bridge is online |

---

## MCP Resources

The server also exposes live data as **MCP Resources** (read-only, auto-refreshed):

| Resource URI                       | Description              |
| ---------------------------------- | ------------------------ |
| `cobalt-strike://beacons/active`   | All active beacons       |
| `cobalt-strike://listeners/active` | All active listeners     |
| `cobalt-strike://bridge/status`    | CNA bridge health status |

---

## Modular CNA Architecture

The Aggressor Script side is structured as a module system for easy extension:

```plaintext
cs_bridge.cna                 ← Entry point: global config + includes + start
modules/
  utils.cna                   ← HTTP helpers: send_json_response, check_auth,
  │                               read_body, parse_json_field
  handlers_beacon.cna         ← All /beacon/* route handlers
  handlers_listener.cna       ← /listeners and /listener/create handlers
  server.cna                  ← Route dispatch (handle_request) + server startup
```

To add a new endpoint:

1. Add a handler `sub handle_xyz` in the appropriate `modules/handlers_*.cna`
2. Add a route entry in `modules/server.cna` → `handle_request`
3. Add a corresponding `@mcp.tool()` in `cs_mcp_bridge.py`

---

## Troubleshooting

### CNA bridge not starting

- Check the Script Console in CS for error messages.
- Ensure port `17777` is not already in use: `netstat -ano | findstr 17777` (Windows).

### `401 Unauthorized` from the Python bridge

- Confirm `CS_BRIDGE_TOKEN` matches `$BRIDGE_TOKEN` in `cs_bridge.cna`.

### `Connection refused` from the Python bridge

- Verify the CNA script is loaded and the bridge is running (check Script Console).
- Confirm `CS_BRIDGE_URL` points to the correct host and port.

### `ModuleNotFoundError: No module named 'fastmcp'`

- Activate your virtual environment before running: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux).
- Then: `pip install httpx fastmcp`.

---

> [!WARNING]
> This tool provides direct access to Cobalt Strike capabilities for adversary simulation.  
> **Use only in environments where you have explicit written authorization to perform security testing.**
