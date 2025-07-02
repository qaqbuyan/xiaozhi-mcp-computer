"""
此脚本用于连接到MCP服务器并将输入输出通过WebSocket端点传输。
版本: 0.1.0

使用方法:

设置环境变量:
export MCP_ENDPOINT=<mcp_endpoint>
运行脚本:
python mcp_pipe.py <mcp_script>
"""

import sys
import yaml
import time
import random
import signal
import asyncio
import logging
import websockets
import subprocess
from handle.logger import setup_logging

# 加载YAML配置（添加encoding='utf-8'参数）
with open('config.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)

logger = setup_logging()
logger = logging.getLogger('管道代理')

# 重连设置
INITIAL_BACKOFF = config['reconnection']['initial_backoff']
MAX_BACKOFF = config['reconnection']['max_backoff']
reconnect_attempt = config['reconnection']['reconnect_attempt']
backoff = config['reconnection']['backoff']

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
        except Exception as e:
            reconnect_attempt += 1
            logger.warning(f"连接关闭(尝试次数: {reconnect_attempt}): {e}")            
            # 计算下次重连等待时间(指数退避)
            backoff = min(backoff * 2, MAX_BACKOFF)

async def connect_to_server(uri, on_process_end=None):
    """连接到WebSocket服务器并与`mcp_script`建立双向通信"""
    global reconnect_attempt, backoff
    try:
        logger.info(f"正在连接WebSocket服务器...")
        async with websockets.connect(uri) as websocket:
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
                encoding='utf-8',
                text=True  # 使用文本模式
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
        if 'process' in locals():
            logger.info("正在终止进程")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info("进程已终止")

async def pipe_websocket_to_process(websocket, process):
    """从WebSocket读取数据并写入进程stdin"""
    try:
        while True:
            # 从WebSocket读取消息
            message = await websocket.recv()
            logger.debug(f"<< {message[:120]}...")
            # 写入进程stdin(文本模式)
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            process.stdin.write(message + '\n')
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
    try:
        while True:
            # 从进程stdout读取数据
            data = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )
            if not data:  # 如果没有数据，进程可能已结束
                logger.info("进程输出已结束")
                if on_process_end:
                    on_process_end()
                break
                
            # 发送数据到WebSocket
            logger.debug(f">> {data[:120]}...")
            # 文本模式下，数据已经是字符串，无需解码
            await websocket.send(data)
    except Exception as e:
        logger.error(f"进程到WebSocket管道错误: {e}")
        raise  # 重新抛出异常以触发重连

async def pipe_process_stderr_to_terminal(process, on_process_end=None):
    """从进程stderr读取数据并打印到终端"""
    try:
        while True:
            # 从进程stderr读取数据
            data = await asyncio.get_event_loop().run_in_executor(
                None, process.stderr.readline
            )
            if not data:  # 如果没有数据，进程可能已结束
                logger.info("进程标准错误输出已结束")
                if on_process_end:
                    on_process_end()
                break
            # 将stderr数据打印到终端(文本模式下，数据已经是字符串)
            sys.stderr.write(data)
            sys.stderr.flush()
    except Exception as e:
        logger.error(f"进程标准错误管道错误: {e}")
        raise  # 重新抛出异常以触发重连

def signal_handler(sig, frame):
    """处理中断信号"""
    logger.info("收到中断信号，正在关闭...")
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
        logger.info("准备运行管道服务")
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
        # 修改此处，移除多余的 on_process_end 参数
        return await connect_with_retry(config['endpoint']['url'])
    except Exception as e:
        logger.error(f"管道服务启动失败: {str(e)}")
        time.sleep(30)  # 等待30秒
        return 1
        if args is None:
            args = sys.argv[1:]

if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    # 启动主循环
    try:
        asyncio.run(main())  # 使用asyncio.run来运行协程
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行错误: {e}")
    main()