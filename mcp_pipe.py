"""
管道服务入口：信号注册、配置加载、启动
"""

import sys
import signal
import atexit
import asyncio
import logging
from handle.loader import load_config
from handle.logger import setup_logging
from handle.ws_connection import set_config
from handle.ws_utils import cleanup_all_processes
from handle.signal_handler import make_signal_handler
from handle.app_entry import main as _app_main

config = load_config()
logger = setup_logging()
logger = logging.getLogger('管道代理')

# 从配置初始化连接参数
set_config(config)

signal_handler = make_signal_handler('管道代理')

if __name__ == "__main__":
    # 注册信号处理器和atexit处理器
    for sig in [signal.SIGINT, signal.SIGTERM]:
        try:
            signal.signal(sig, signal_handler)
        except (OSError, ValueError):
            pass
    atexit.register(cleanup_all_processes)

    try:
        asyncio.run(_app_main(config, logger))
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        from handle.ws_utils import translate_ws_error
        logger.error(f"程序执行错误: {translate_ws_error(e)}")