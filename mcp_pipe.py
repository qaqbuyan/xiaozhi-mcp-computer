import sys
import time
import json
import ssl
import random
import signal
import atexit
import asyncio
import logging
import websockets
import subprocess
from handle.loader import load_config
from handle.logger import setup_logging

config = load_config()
logger = setup_logging()
logger = logging.getLogger('管道代理')

# 重连设置
INITIAL_BACKOFF = config['reconnection']['initial_backoff']
MAX_BACKOFF = config['reconnection']['max_backoff']
reconnect_attempt = config['reconnection']['reconnect_attempt']
backoff = config['reconnection']['backoff']

# 标记是否已输出过 SSL 错误引导信息
_ssl_error_guided = False

def _is_ssl_error(error: Exception) -> bool:
    """判断异常是否为 SSL 证书错误"""
    error_str = str(error).lower()
    ssl_keywords = [
        'certificate verify failed',
        'self-signed certificate',
        'certificate has expired',
        'ssl',
        'sslv3',
        'tls',
    ]
    return any(kw in error_str for kw in ssl_keywords)


def _is_self_signed_cert_error(error: Exception) -> bool:
    """判断是否为自签名证书链错误（self-signed certificate in certificate chain）
    此类错误由客户端网络环境的 SSL 中间人审查导致，重试也无法恢复。
    """
    return 'self-signed certificate in certificate chain' in str(error).lower()


def _is_dns_error(error: Exception) -> bool:
    """判断是否为 DNS 解析失败错误（getaddrinfo failed / Name or service not known）
    此类错误由网络断开、DNS 异常或域名不存在导致，重试也无法恢复。
    """
    error_str = str(error).lower()
    return ('getaddrinfo failed' in error_str
            or 'name or service not known' in error_str
            or 'temporary failure in name resolution' in error_str)


_dns_error_guided = False


def _log_dns_guidance():
    """输出 DNS 解析错误的用户引导信息（仅首次输出）"""
    global _dns_error_guided
    if _dns_error_guided:
        return
    _dns_error_guided = True
    guidance = (
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║  DNS 解析失败，无法找到服务器地址                             ║\n"
        "╠══════════════════════════════════════════════════════════════╣\n"
        "║  这是客户端网络环境问题，常见原因及解决方法：                 ║\n"
        "║  1. 网络未连接 → 请检查网络是否正常                          ║\n"
        "║  2. DNS 服务器异常 → 尝试将 DNS 改为 114.114.114.114         ║\n"
        "║     或 8.8.8.8 后重试                                         ║\n"
        "║  3. 域名解析被拦截 → 检查代理/VPN 配置或切换手机热点测试     ║\n"
        "╚══════════════════════════════════════════════════════════════╝"
    )
    logger.warning(f"\n{guidance}")


def _log_ssl_guidance():
    """输出 SSL 证书错误的用户引导信息（仅首次输出）"""
    global _ssl_error_guided
    if _ssl_error_guided:
        return
    _ssl_error_guided = True
    guidance = (
        "╔══════════════════════════════════════════════════════════════╗\n"
        "║  SSL 证书验证失败，无法安全连接到服务器                      ║\n"
        "╠══════════════════════════════════════════════════════════════╣\n"
        "║  这是客户端网络环境问题，常见原因及解决方法：                 ║\n"
        "║  1. 系统时间不正确 → 请校准系统时间后再试                    ║\n"
        "║  2. 公司/学校网络开启了 SSL 审查（代理拦截）                  ║\n"
        "║     → 请关闭代理/VPN，或切换到手机热点网络测试               ║\n"
        "║  3. 杀毒软件（如 360、卡巴斯基）启用了 HTTPS 扫描            ║\n"
        "║     → 请在杀毒软件中关闭 HTTPS/SSL 扫描功能                  ║\n"
        "╚══════════════════════════════════════════════════════════════╝"
    )
    logger.warning(f"\n{guidance}")


def cleanup_all_processes():
    """清理所有相关进程的全局函数"""
    logger.info("开始全局进程清理...")
    try:
        from utils.music.play import GlobalProcessManager
        process_manager = GlobalProcessManager()
        process_manager.cleanup_all_processes()
        logger.info("全局进程清理完成")
    except ImportError:
        logger.info("音乐模块未加载，跳过进程清理")
    except Exception as e:
        logger.error(f"全局进程清理出错: {str(e)}")

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，开始优雅退出...")
    cleanup_all_processes()
    sys.exit(0)

# 注册信号处理器和atexit处理器
for sig in [signal.SIGINT, signal.SIGTERM]:
    try:
        signal.signal(sig, signal_handler)
    except (OSError, ValueError):
        pass

atexit.register(cleanup_all_processes)

async def connect_with_retry(uri):
    """带重试机制的WebSocket服务器连接"""
    global reconnect_attempt, backoff
    while True:  # 无限重连
        try:
            if reconnect_attempt > 0:
                wait_time = backoff * (1 + random.random() * 0.1)  # 添加随机抖动
                logger.info(f"等待 {wait_time:.2f} 秒后进行第 {reconnect_attempt} 次重连尝试...")
                await asyncio.sleep(wait_time)
            # 尝试连接
            await connect_to_server(uri)
        except ssl.SSLError as e:
            reconnect_attempt += 1
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {e}")
            if _is_self_signed_cert_error(e):
                _log_ssl_guidance()
                logger.error("自签名证书链错误无法通过重试解决，停止连接")
                return 1
            _log_ssl_guidance()
            # 其他 SSL 错误（如证书过期）继续重试，万一用户手动修复了问题
            backoff = min(backoff * 2, MAX_BACKOFF)
        except websockets.exceptions.WebSocketException as e:
            reconnect_attempt += 1
            error_str = str(e)
            if _is_self_signed_cert_error(e):
                _log_ssl_guidance()
                logger.error("自签名证书链错误无法通过重试解决，停止连接")
                return 1
            if _is_dns_error(e):
                _log_dns_guidance()
                logger.error("DNS 解析失败无法通过重试解决，停止连接")
                return 1
            if _is_ssl_error(e):
                _log_ssl_guidance()
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {error_str}")
            # 超时类错误不增加退避时间，直接快速重试
            if 'timed out' in error_str:
                backoff = INITIAL_BACKOFF
            else:
                backoff = min(backoff * 2, MAX_BACKOFF)
        except Exception as e:
            reconnect_attempt += 1
            error_str = str(e)
            if _is_self_signed_cert_error(e):
                _log_ssl_guidance()
                logger.error("自签名证书链错误无法通过重试解决，停止连接")
                return 1
            if _is_dns_error(e):
                _log_dns_guidance()
                logger.error("DNS 解析失败无法通过重试解决，停止连接")
                return 1
            if _is_ssl_error(e):
                _log_ssl_guidance()
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {error_str}")
            # 超时类错误不增加退避时间，直接快速重试
            if 'timed out' in error_str:
                backoff = INITIAL_BACKOFF
            else:
                backoff = min(backoff * 2, MAX_BACKOFF)

async def connect_to_server(uri, on_process_end=None):
    """连接到WebSocket服务器并与`mcp_script`建立双向通信"""
    global reconnect_attempt, backoff
    try:
        logger.info(f"正在连接WebSocket服务器...")
        try:
            websocket = await websockets.connect(uri, open_timeout=5)
        except ssl.SSLCertVerificationError as e:
            _log_ssl_guidance()
            raise
        except websockets.exceptions.WebSocketException as e:
            if _is_dns_error(e):
                _log_dns_guidance()
            if _is_ssl_error(e):
                _log_ssl_guidance()
            raise
        except OSError as e:
            if _is_dns_error(e):
                _log_dns_guidance()
            raise
        async with websocket:
            logger.info(f"成功连接到WebSocket服务器")
            # 如果连接正常关闭，重置重连计数器
            reconnect_attempt = 0
            backoff = INITIAL_BACKOFF
            # 启动mcp_script进程
            process = subprocess.Popen(
                ['python', mcp_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding=None,  # 不设置编码，使用二进制模式
                text=False  # 使用二进制模式
            )
            logger.info(f"已启动注册进程")
            # 创建两个任务：从WebSocket读取并写入进程，从进程读取并写入WebSocket
            await asyncio.gather(
                pipe_websocket_to_process(websocket, process),
                pipe_process_to_websocket(process, websocket, on_process_end),
                pipe_process_stderr_to_terminal(process, on_process_end)
            )
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket连接关闭: {e}")
        raise  # 重新抛出异常以触发重连
    except Exception as e:
        logger.error(f"连接错误: {e}")
        raise  # 重新抛出异常
    finally:
        # 确保子进程被正确终止
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
            logger.error(f"清理进程时出错: {cleanup_error}")
        
        # 清理所有音乐相关进程
        try:
            from utils.music.play import GlobalProcessManager
            process_manager = GlobalProcessManager()
            process_manager.cleanup_all_processes()
        except ImportError:
            pass  # 如果音乐模块未加载，跳过清理
        except Exception as music_cleanup_error:
            logger.error(f"清理音乐进程时出错: {music_cleanup_error}")

async def pipe_websocket_to_process(websocket, process):
    """从WebSocket读取数据并写入进程stdin"""
    try:
        while True:
            # 从WebSocket读取消息
            message = await websocket.recv()
            logger.info("收到响应...")
            # 处理编码问题：先尝试UTF-8，失败则尝试GBK
            if isinstance(message, bytes):
                try:
                    message = message.decode('utf-8')
                except UnicodeDecodeError:
                    message = message.decode('gbk')
            # 将消息转换为字节并写入进程stdin
            process.stdin.write(message.encode('utf-8') + b'\n')
            process.stdin.flush()
    except Exception as e:
        logger.error(f"WebSocket到进程管道错误: {e}")
        raise  # 重新抛出异常以触发重连
    finally:
        # 关闭进程stdin
        if not process.stdin.closed:
            process.stdin.close()

async def pipe_process_to_websocket(process, websocket, on_process_end=None):
    """从进程stdout读取数据并发送到WebSocket"""
    printed = False
    try:
        while True:
            # 读取二进制数据
            data_bytes = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )
            if not data_bytes:
                logger.info("进程输出已结束")
                break
            
            # 处理编码问题：先尝试UTF-8，失败则尝试GBK
            try:
                data = data_bytes.decode('utf-8')
            except UnicodeDecodeError:
                data = data_bytes.decode('gbk')
            
            try:
                json_data = json.loads(data.strip())
                if json_data.get('id') == 1 and not printed:
                    if 'result' in json_data and 'tools' in json_data['result']:
                        for tool in json_data['result']['tools']:
                            name = tool.get('name', '')
                            description = tool.get('description', '')
                            first_line = description.split('\n')[0]
                            logger.debug(f"{name} - {first_line}")
                        logger.info('已注册工具数量：%d' % len(json_data['result']['tools']))
                    printed = True
            except json.JSONDecodeError:
                pass
            logger.info("发送响应...")
            await websocket.send(data)
    except Exception as e:
        logger.error(f"进程到WebSocket管道错误: {e}")
        raise

async def pipe_process_stderr_to_terminal(process, on_process_end=None):
    """从进程stderr读取数据并打印到终端"""
    try:
        while True:
            # 从进程stderr读取二进制数据
            data_bytes = await asyncio.get_event_loop().run_in_executor(
                None, process.stderr.readline
            )
            if not data_bytes:  # 如果没有数据，进程可能已结束
                logger.info("进程标准错误输出已结束")
                if on_process_end:
                    on_process_end()
                break
            
            # 处理编码问题：先尝试UTF-8，失败则尝试GBK
            try:
                data = data_bytes.decode('utf-8')
            except UnicodeDecodeError:
                data = data_bytes.decode('gbk')
            
            # 将stderr数据打印到终端
            sys.stderr.write(data)
            sys.stderr.flush()
    except Exception as e:
        logger.error(f"进程标准错误管道错误: {e}")
        raise  # 重新抛出异常以触发重连

def signal_handler(sig, frame):
    """处理中断信号"""
    logger.info(f"收到中断信号 {sig}，正在关闭...")
    cleanup_all_processes()
    sys.exit(0)

async def main(args=None, on_process_end=None):
    """管道服务主入口函数"""
    try:
        if args is None:
            args = sys.argv[1:]
        if not args:
            logger.error("请指定要运行的管道服务代理路径")
            time.sleep(30)  # 等待30秒
            return 1
        global mcp_script
        mcp_script = args[0]
        logger.info("准备运行管道服务...")
        # 检查配置文件格式
        if not config.get('endpoint') or not isinstance(config['endpoint'], dict):
            logger.error("请确认配置，该配置是无效的")
            time.sleep(30)  # 等待30秒
            return 1
        endpoint_url = config['endpoint'].get('url', '')
        # 验证endpoint格式
        if not endpoint_url.startswith(('wss://', 'ws://')):
            logger.error("请确认配置，WebSocket端点URL必须以wss://或ws://开头")
            time.sleep(30)  # 等待30秒
            return 1
        return await connect_with_retry(config['endpoint']['url'])
    except Exception as e:
        logger.error(f"管道服务启动失败: {str(e)}")
        time.sleep(30)  # 等待30秒
        return 1

if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    # 启动主循环
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行错误: {e}")