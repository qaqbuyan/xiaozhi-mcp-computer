import os
import ssl
import random
import asyncio
import logging
import subprocess
import websockets
from handle.ws_utils import (
    is_ssl_error, is_self_signed_cert_error, is_dns_error,
    translate_ws_error, log_dns_guidance, log_ssl_guidance, cleanup_all_processes,
)
from handle.ws_pipe import (
    pipe_websocket_to_process, pipe_process_to_websocket, pipe_process_stderr_to_terminal,
)

logger = logging.getLogger('管道代理')

# ---------- 连接状态 ----------
reconnect_attempt = 0
backoff = 1
INITIAL_BACKOFF = 1
MAX_BACKOFF = 60
mcp_script = None

def set_config(config: dict):
    """从配置中初始化重连参数"""
    global INITIAL_BACKOFF, MAX_BACKOFF, reconnect_attempt, backoff
    reconnect_attempt = config['reconnection']['reconnect_attempt']
    backoff = config['reconnection']['backoff']
    INITIAL_BACKOFF = config['reconnection']['initial_backoff']
    MAX_BACKOFF = config['reconnection']['max_backoff']

def set_mcp_script(script_path: str):
    """设置 MCP 脚本路径"""
    global mcp_script
    mcp_script = script_path

async def connect_with_retry(uri):
    """带重试机制的WebSocket服务器连接"""
    global reconnect_attempt, backoff
    while True:
        try:
            if reconnect_attempt > 0:
                wait_time = backoff * (1 + random.random() * 0.1)
                logger.info(f"等待 {wait_time:.2f} 秒后进行第 {reconnect_attempt} 次重连尝试...")
                await asyncio.sleep(wait_time)
            await connect_to_server(uri)
        except ssl.SSLError as e:
            reconnect_attempt += 1
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {translate_ws_error(e)}")
            if is_self_signed_cert_error(e):
                log_ssl_guidance()
                logger.error("自签名证书链错误无法通过重试解决，停止连接")
                return 1
            log_ssl_guidance()
            backoff = min(backoff * 2, MAX_BACKOFF)
        except websockets.exceptions.WebSocketException as e:
            reconnect_attempt += 1
            error_str = str(e)
            if is_self_signed_cert_error(e):
                log_ssl_guidance()
                logger.error("自签名证书链错误无法通过重试解决，停止连接")
                return 1
            if is_dns_error(e):
                log_dns_guidance()
                logger.error("DNS 解析失败无法通过重试解决，停止连接")
                return 1
            if is_ssl_error(e):
                log_ssl_guidance()
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {translate_ws_error(error_str)}")
            if 'timed out' in error_str:
                backoff = INITIAL_BACKOFF
            else:
                backoff = min(backoff * 2, MAX_BACKOFF)
        except Exception as e:
            reconnect_attempt += 1
            error_str = str(e)
            if is_self_signed_cert_error(e):
                log_ssl_guidance()
                logger.error("自签名证书链错误无法通过重试解决，停止连接")
                return 1
            if is_dns_error(e):
                log_dns_guidance()
                logger.error("DNS 解析失败无法通过重试解决，停止连接")
                return 1
            if is_ssl_error(e):
                log_ssl_guidance()
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {translate_ws_error(error_str)}")
            if 'timed out' in error_str:
                backoff = INITIAL_BACKOFF
            else:
                backoff = min(backoff * 2, MAX_BACKOFF)

async def connect_to_server(uri, on_process_end=None):
    """连接到WebSocket服务器并与`mcp_script`进程建立双向通信"""
    global reconnect_attempt, backoff
    try:
        logger.info("正在连接WebSocket服务器...")
        try:
            websocket = await websockets.connect(uri, open_timeout=5)
        except ssl.SSLCertVerificationError as e:
            log_ssl_guidance()
            raise
        except websockets.exceptions.WebSocketException as e:
            if is_dns_error(e):
                log_dns_guidance()
            if is_ssl_error(e):
                log_ssl_guidance()
            raise
        except OSError as e:
            if is_dns_error(e):
                log_dns_guidance()
            raise
        async with websocket:
            logger.info("成功连接到WebSocket服务器")
            reconnect_attempt = 0
            backoff = INITIAL_BACKOFF
            env = os.environ.copy()
            from handle.path import get_config_path
            env['MCP_CONFIG_PATH'] = get_config_path()
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                creationflags |= subprocess.CREATE_NO_WINDOW
            
            process = subprocess.Popen(
                ['python', mcp_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding=None,
                text=False,
                env=env,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            logger.info("已启动注册进程")
            await asyncio.gather(
                pipe_websocket_to_process(websocket, process),
                pipe_process_to_websocket(process, websocket, on_process_end),
                pipe_process_stderr_to_terminal(process, on_process_end)
            )
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket连接关闭: {translate_ws_error(e)}")
        raise
    except Exception as e:
        logger.error(f"连接错误: {translate_ws_error(e)}")
        raise
    finally:
        try:
            if 'process' in locals() and process.poll() is None:
                logger.info("正在终止进程")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
                logger.info("进程已终止")
        except Exception as cleanup_error:
            logger.error(f"清理进程时出错: {translate_ws_error(cleanup_error)}")

        try:
            from utils.music.play import GlobalProcessManager
            process_manager = GlobalProcessManager()
            process_manager.cleanup_all_processes()
        except ImportError:
            pass
        except Exception as music_cleanup_error:
            logger.error(f"清理音乐进程时出错: {translate_ws_error(music_cleanup_error)}")