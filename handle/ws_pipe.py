import sys
import json
import asyncio
import logging
from handle.ws_utils import translate_ws_error

logger = logging.getLogger('管道代理')

async def pipe_websocket_to_process(websocket, process):
    """从WebSocket读取数据并写入进程stdin"""
    try:
        while True:
            message = await websocket.recv()
            logger.info("收到响应...")
            if isinstance(message, bytes):
                try:
                    message = message.decode('utf-8')
                except UnicodeDecodeError:
                    message = message.decode('gbk')
            process.stdin.write(message.encode('utf-8') + b'\n')
            process.stdin.flush()
    except Exception as e:
        logger.error(f"WebSocket到进程管道错误: {translate_ws_error(e)}")
        raise
    finally:
        if not process.stdin.closed:
            process.stdin.close()

async def pipe_process_to_websocket(process, websocket, on_process_end=None):
    """从进程stdout读取数据并发送到WebSocket"""
    printed = False
    try:
        while True:
            data_bytes = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )
            if not data_bytes:
                logger.info("进程输出已结束")
                break

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
        logger.error(f"进程到WebSocket管道错误: {translate_ws_error(e)}")
        raise

async def pipe_process_stderr_to_terminal(process, on_process_end=None):
    """从进程stderr读取数据并打印到终端"""
    try:
        while True:
            data_bytes = await asyncio.get_event_loop().run_in_executor(
                None, process.stderr.readline
            )
            if not data_bytes:
                logger.info("进程标准错误输出已结束")
                if on_process_end:
                    on_process_end()
                break

            try:
                data = data_bytes.decode('utf-8')
            except UnicodeDecodeError:
                data = data_bytes.decode('gbk')

            sys.stderr.write(data)
            sys.stderr.flush()
    except Exception as e:
        logger.error(f"进程标准错误管道错误: {translate_ws_error(e)}")
        raise