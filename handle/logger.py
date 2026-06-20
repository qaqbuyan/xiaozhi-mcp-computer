import os
import logging
from datetime import datetime


class SingleLineFormatter(logging.Formatter):
    """保证每条日志只占一行的格式化器"""
    def format(self, record):
        msg = super().format(record)
        # 将消息中的换行符转为可见转义符，确保一行一条日志
        msg = msg.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
        return msg


def setup_logging():
    """日志配置"""
    logger = logging.getLogger('管道服务')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s：%(levelname)s，%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.addLevelName(logging.INFO, "信息")
    logging.addLevelName(logging.WARNING, "警告") 
    logging.addLevelName(logging.ERROR, "错误")
    logging.addLevelName(logging.CRITICAL, "严重错误")
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    today = datetime.today().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(SingleLineFormatter('%(asctime)s - %(name)s：%(levelname)s，%(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    root_logger = logging.getLogger('')
    # 检查是否已经存在相同的文件处理器
    if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == os.path.abspath(log_file) for handler in root_logger.handlers):
        root_logger.addHandler(file_handler)
    return logger