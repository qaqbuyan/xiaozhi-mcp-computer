import os
import logging
from datetime import datetime
from handle.color_formatter import ColoredFormatter

class SingleLineFormatter(logging.Formatter):
    """保证每条日志只占一行的格式化器"""
    def format(self, record):
        msg = super().format(record)
        # 将消息中的换行符转为可见转义符，确保一行一条日志
        msg = msg.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
        return msg


class RootLoggerFilter(logging.Filter):
    """将 root 日志器的名称改为"管道服务"，并翻译特定的英文日志消息"""
    _msg_translations = {
        'Failed to validate request: Received request before initialization was complete':
            '未能验证请求：在初始化完成前收到请求',
    }

    def filter(self, record):
        if record.name == 'root':
            record.name = '管道服务'
        msg = record.getMessage()
        if msg in self._msg_translations:
            record.msg = self._msg_translations[msg]
            record.args = ()
        return True


def setup_logging():
    """日志配置"""
    logger = logging.getLogger('管道服务')

    # 配置中文化级别名称
    logging.addLevelName(logging.INFO, "信息")
    logging.addLevelName(logging.WARNING, "警告") 
    logging.addLevelName(logging.ERROR, "错误")
    logging.addLevelName(logging.CRITICAL, "严重错误")

    fmt = '%(asctime)s - %(name)s：%(levelname)s，%(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'

    # 手动配置 root logger
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(fmt, datefmt=datefmt))
    root_logger.addHandler(console_handler)

    # 文件处理器
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    today = datetime.today().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(SingleLineFormatter(fmt, datefmt=datefmt))
    root_logger.addHandler(file_handler)

    # 为 root 日志器添加过滤器（改名 + 翻译）
    root_logger.addFilter(RootLoggerFilter())

    return logger