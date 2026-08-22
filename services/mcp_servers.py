
import os
import sys
import yaml
import asyncio
import logging
import pydantic
from typing import Any
from handle.loader import load_config
from mcp.server.fastmcp import FastMCP
from handle.path import get_config_path

logger = logging.getLogger('三方服务')

def _install_httpx_log_filter() -> None:
    """注入 httpx 日志过滤器：隐藏 "HTTP Request: ..." 信息日志（含完整 URL/凭据），
    请求状态由客户端在调用工具后以简洁日志代替。"""
    httpx_logger = logging.getLogger('httpx')

    class _HttpxInfoFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno >= logging.WARNING

    httpx_logger.addFilter(_HttpxInfoFilter())

_install_httpx_log_filter()

def _install_streamable_http_log_filter() -> None:
    """注入 mcp.client.streamable_http 日志过滤器：将协议版本协商日志翻译为中文，
    并将日志器名称改为"流式传输"。"""
    streamable_logger = logging.getLogger('mcp.client.streamable_http')

    class _ProtocolVersionFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            msg = record.getMessage()
            prefix = 'Negotiated protocol version: '
            if msg.startswith(prefix):
                record.msg = f'协商协议版本：{msg[len(prefix):]}'
                record.args = ()
                record.name = '流式传输'
            return True

    streamable_logger.addFilter(_ProtocolVersionFilter())

_install_streamable_http_log_filter()

# 已注册的第三方 MCP 服务器客户端，供服务关闭时统一释放连接
_ACTIVE_CLIENTS = []
HTTP_METHOD_KEYS = ('url', 'headers')
STDIO_METHOD_KEYS = ('command', 'args', 'env')

class McpServerClient:
    """第三方 MCP 服务器客户端（懒连接，首次调用工具时建立连接并复用）"""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config or {}
        self._client = None
        self._read = None
        self._write = None
        self._session = None
        self._closed = False
        self._lock = asyncio.Lock()
        self._last_http_status = None

    def _create_session(self):
        """根据配置创建连接客户端，支持 HTTP（Streamable HTTP）和 stdio 命令两种方式"""
        from mcp import ClientSession

        if self.config.get('url'):
            from mcp.client.streamable_http import streamablehttp_client, create_mcp_http_client

            url = self.config['url']
            headers = self.config.get('headers') or {}
            headers = {
                str(key): str(value)
                for key, value in headers.items()
                if value is not None and str(value).strip()
            }

            # 注入 httpx 响应钩子，捕获每次请求的 HTTP 状态码，用于输出简洁的请求日志
            def _build_client_factory():
                def factory(headers, timeout, auth):
                    client = create_mcp_http_client(headers, timeout, auth)

                    async def _record_status(response):
                        self._last_http_status = response.status_code

                    client.event_hooks.setdefault('response', []).append(_record_status)
                    return client

                return factory

            self._client = streamablehttp_client(
                url, headers=headers, httpx_client_factory=_build_client_factory()
            )
        else:
            from mcp.client.stdio import StdioServerParameters, stdio_client

            params = StdioServerParameters(
                command=self.config.get('command') or '',
                args=self.config.get('args') or [],
                env=self.config.get('env'),
            )
            self._client = stdio_client(params)
        return ClientSession

    async def ensure_session(self):
        """获取可用的会话，不存在时建立连接"""
        async with self._lock:
            if self._closed:
                raise RuntimeError(f"第三方 MCP 服务器 {self.name} 已关闭")
            if self._session is not None:
                return self._session
            session_cls = self._create_session()
            # streamablehttp_client 返回 3 元组，stdio_client 返回 2 元组，这里按索引兼容
            entered = await self._client.__aenter__()
            self._read, self._write = entered[0], entered[1]
            self._session = session_cls(self._read, self._write)
            await self._session.__aenter__()
            await self._session.initialize()
            logger.info(f"第三方 MCP 服务器 {self.name} 连接成功")
            return self._session

    async def list_tools(self):
        """获取服务器提供的全部工具"""
        session = await self.ensure_session()
        result = await session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """调用服务器的某个工具"""
        session = await self.ensure_session()
        result = await session.call_tool(tool_name, arguments)
        status = self._last_http_status
        status_text = f"{status} ok" if status else "ok"
        logger.info(f"请求第三方 MCP 服务器 {self.name} 工具 {tool_name} {status_text}")
        is_error = getattr(result, 'isError', False)
        detail = _format_result(result)
        logger.info(
            f"第三方 MCP 服务器 {self.name} 工具 {tool_name} 返回"
            f"（isError={is_error}，参数 {arguments}）：\n{detail}"
        )
        return result

    async def close(self):
        """关闭连接并清理资源"""
        async with self._lock:
            if self._closed:
                return
            self._closed = True
            if self._session is not None:
                try:
                    await self._session.__aexit__(None, None, None)
                except Exception:
                    pass
                self._session = None
            if self._client is not None:
                try:
                    await self._client.__aexit__(None, None, None)
                except Exception:
                    pass
                self._client = None
            logger.info(f"第三方 MCP 服务器 {self.name} 连接已关闭")

_JSON_TYPE_MAP = {
    'string': str,
    'number': float,
    'integer': int,
    'boolean': bool,
    'array': list,
    'object': dict,
    'null': type(None),
}

def _map_json_type(prop: dict) -> type:
    """将 JSON Schema 的属性类型映射为 Python 类型，无法映射的字段使用 Any 兜底"""
    prop_type = prop.get('type')
    if isinstance(prop_type, list):
        return Any
    if prop_type in _JSON_TYPE_MAP:
        return _JSON_TYPE_MAP[prop_type]
    if any(key in prop for key in ('anyOf', 'oneOf', 'allOf', '$ref', 'enum')):
        return Any
    return Any

def _build_params_model(tool_name: str, input_schema: dict):
    """根据远程工具的参数 Schema 动态构建参数模型"""
    schema = input_schema or {}
    properties = schema.get('properties') or {}
    required = set(schema.get('required') or [])
    fields = {}
    for name, prop in properties.items():
        description = prop.get('description') or ''
        field_type = _map_json_type(prop)
        if name in required:
            fields[name] = (field_type, pydantic.Field(description=description))
        else:
            fields[name] = (field_type, pydantic.Field(default=None, description=description))
    return pydantic.create_model(f'{tool_name}Params', **fields)

def _format_result(result):
    """将远程工具调用结果转换为可返回给 AI 的数据"""
    structured = getattr(result, 'structuredContent', None)
    if structured is not None:
        return structured
    parts = []
    for block in result.content or []:
        text = getattr(block, 'text', None)
        if text is not None:
            parts.append(text)
            continue
        data = getattr(block, 'data', None)
        if data is not None:
            parts.append(f'[二进制数据: {len(data)} 字节]')
            continue
        parts.append(str(block))
    text = '\n'.join(parts)
    if getattr(result, 'isError', False) and not text:
        text = f"调用失败：{result}"
    return text

def _safe_name(name: str) -> str:
    """将名称转换为 MCP 工具名允许的字符（字母/数字/下划线/连字符）"""
    import re
    return re.sub(r'[^A-Za-z0-9_-]', '_', name)

def _register_passthrough_tool(mcp: FastMCP, client: McpServerClient, tool):
    """将远程工具注册为本地透传工具"""
    params_model = _build_params_model(tool.name, tool.inputSchema)
    remote_name = tool.name
    local_name = f"{_safe_name(client.name)}_{_safe_name(tool.name)}"
    description = tool.description or f"第三方 MCP 服务器 {client.name} 提供的工具 {tool.name}"

    async def passthrough(params) -> Any:
        arguments = params.model_dump(exclude_none=True)
        result = await client.call_tool(remote_name, arguments)
        return _format_result(result)

    # 动态创建的参数模型不能直接作为源码注解（会被类型检查器或 typing 报
    # “类型表达式中不允许使用变量”），改为在注册前显式写入函数注解，
    # 并注入模块全局命名空间，确保 FastMCP 解析注解时能拿到该模型。
    passthrough.__annotations__['params'] = params_model
    passthrough.__globals__['params_model'] = params_model
    mcp.add_tool(passthrough, name=local_name, description=description)

def _validate_invocation_method(name: str, server_config: dict) -> bool:
    """校验单个服务器条目的调用方式配置。

    返回 True 表示配置合法可注册；
    缺少参数或无内容的条目输出日志并返回 False（直接跳过该服务器）；
    同时配置 HTTP 与 stdio 的冲突配置属于明确错误，直接停止执行。
    """
    server_config = server_config or {}
    has_http = any(key in server_config for key in HTTP_METHOD_KEYS)
    has_stdio = any(key in server_config for key in STDIO_METHOD_KEYS)

    if has_http and has_stdio:
        logger.error(
            f"第三方 MCP 服务器 {name} 配置错误：不能同时配置 HTTP（url/headers）"
            f"和 stdio（command/args/env）两种调用方式，请二选一，程序将停止执行"
        )
        sys.exit(1)

    if not has_http and not has_stdio:
        logger.warning(
            f"第三方 MCP 服务器 {name} 缺少调用方式配置"
            f"（url/headers 或 command/args/env），已跳过"
        )
        return False

    if has_http and not server_config.get('url'):
        logger.warning(
            f"第三方 MCP 服务器 {name} 配置不完整：HTTP 方式缺少 url 端点（当前为空），已跳过"
        )
        return False

    if has_stdio and not server_config.get('command'):
        logger.warning(
            f"第三方 MCP 服务器 {name} 配置不完整：stdio 方式缺少 command 启动命令（当前为空），已跳过"
        )
        return False

    return True

def _detect_duplicate_mcp_server_names() -> list:
    """检测 config.yaml 中 mcpServers 是否存在重复的服务器名称

    由于 yaml.safe_load 遇到重复键时会静默覆盖，这里直接检查原始 YAML 结构，
    找出被填写了相同名称（如 FeishuProjectMcp 写了两遍）的服务器。
    """
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return []

    try:
        with open(config_path, encoding='utf-8') as f:
            text = f.read()
        root = yaml.compose(text)
    except Exception:
        return []

    if not isinstance(root, yaml.MappingNode):
        return []

    for key_node, value_node in root.value:
        if key_node.value != 'mcpServers' or not isinstance(value_node, yaml.MappingNode):
            continue
        seen = {}
        for sub_key, _ in value_node.value:
            name = sub_key.value
            seen[name] = seen.get(name, 0) + 1
        return [name for name, count in seen.items() if count > 1]
    return []

def validate_mcp_servers() -> dict:
    """校验 config.yaml 中的 mcpServers 配置（重复名称 + 调用方式），
    返回可注册的服务器配置；缺少参数或无内容的条目输出日志并跳过，
    重复名称或同时配置 HTTP 与 stdio 的冲突配置仍会停止执行。
    只做校验，不建立连接，实际连接在服务启动时由 register_mcp_servers_async 建立。
    """
    # 防止同一服务器名称被重复填写（同一名称只能配置一个第三方 MCP 服务）
    duplicates = _detect_duplicate_mcp_server_names()
    if duplicates:
        logger.error(
            f"检测到 mcpServers 中存在重复的服务器名称 {duplicates}，"
            f"同一名称只能配置一个第三方 MCP 服务，为防止配置冲突，程序将停止执行"
        )
        sys.exit(1)

    config = load_config()
    servers = config.get('mcpServers') or {}
    if not servers:
        logger.info("未配置第三方 MCP 服务器，跳过注册")
        return {}

    # 逐个校验每个服务器条目的调用方式，缺少参数或无内容的条目直接跳过
    valid_servers = {}
    for name, server_config in servers.items():
        if _validate_invocation_method(name, server_config):
            valid_servers[name] = server_config
    if not valid_servers:
        logger.info("所有第三方 MCP 服务器均未启用或配置不合法，跳过注册")
        return {}
    return valid_servers

async def register_mcp_servers_async(mcp: FastMCP):
    """在服务主事件循环中逐个连接并注册第三方 MCP 服务器。

    连接建立后保持打开（长连接），供后续工具调用复用，直到服务关闭时统一释放。
    """
    servers = validate_mcp_servers()
    if not servers:
        return

    logger.info(f"开始注册第三方 MCP 服务器，共 {len(servers)} 个...")
    for name, server_config in servers.items():
        try:
            client = McpServerClient(name, server_config)
            await client.ensure_session()
            tools = await client.list_tools()
            if not tools:
                logger.warning(f"第三方 MCP 服务器 {name} 未提供任何工具，跳过")
                await client.close()
                continue
            _ACTIVE_CLIENTS.append(client)
            for tool in tools:
                _register_passthrough_tool(mcp, client, tool)
            logger.info(f"第三方 MCP 服务器 {name} 注册完成，共 {len(tools)} 个工具")
        except Exception as e:
            logger.error(f"注册第三方 MCP 服务器 {name} 失败：{e}")

async def close_all():
    """关闭所有已注册的第三方 MCP 服务器连接（供服务关闭时调用）"""
    for client in list(_ACTIVE_CLIENTS):
        try:
            await client.close()
        except Exception as e:
            logger.error(f"关闭第三方 MCP 服务器 {client.name} 失败：{e}")
    _ACTIVE_CLIENTS.clear()