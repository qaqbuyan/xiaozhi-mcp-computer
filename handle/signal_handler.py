import os
import logging
from handle.ws_utils import cleanup_all_processes

def make_signal_handler(logger_name='管道服务'):
    """创建一个绑定到指定日志器的信号处理器

    Args:
        logger_name: 日志器名称，默认为 '管道服务'

    Returns:
        function: 符合 signal.signal 回调签名的信号处理函数 (signum, frame) -> None
    """

    def signal_handler(signum, frame):
        logger = logging.getLogger(logger_name)
        logger.info(f"收到信号 {signum}，开始优雅退出...")
        cleanup_all_processes()
        # 使用 os._exit 而非 sys.exit：避免在 asyncio 事件循环中抛出 SystemExit
        # 引发级联异常和未捕获的任务异常
        os._exit(0)

    return signal_handler
