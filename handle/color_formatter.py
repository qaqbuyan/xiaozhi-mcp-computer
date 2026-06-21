import os
import sys
import re
import ctypes
import logging

# Windows 控制台启用 ANSI 颜色支持
def _enable_ansi_on_windows():
    """启用 Windows 终端 ANSI 颜色处理（适用于 cmd.exe 和打包程序）"""
    if sys.platform == 'win32':
        try:
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass

_enable_ansi_on_windows()

# ANSI 颜色转义码
RESET = '\033[0m'
WHITE = '\033[37m'
BLUE = '\033[34m'
YELLOW = '\033[33m'
RED = '\033[31m'
MAGENTA = '\033[35m'

# 日志级别颜色映射
LEVEL_COLORS = {
    '信息': '\033[32m',        # 绿色
    '警告': YELLOW,            # 黄色
    '错误': RED,               # 红色
    '严重错误': MAGENTA,       # 紫色
}

# Logger 名称颜色映射（所有logger名称显示为蓝色）
LOGGER_COLOR = BLUE

class ColoredFormatter(logging.Formatter):
    """分段着色日志格式化器

    格式：%(asctime)s - %(name)s：%(levelname)s，%(message)s

    着色规则：
        - 日期时间：白色
        - 分隔符 " - "：白色
        - logger名称：蓝色
        - 分隔符 "："（第一个）：白色
        - 第一个 ： 到第二个 ： 之间的内容（级别名+消息）：按级别着色
        - 分隔符 "："（第二个）及之后的内容：白色
    """

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self._reset = RESET

    def format(self, record):
        raw_msg = super().format(record)

        # 解析格式：时间 - 名称：级别，消息  [分隔符 后续]
        # 第二个分隔符支持全角 ：或半角 :（如 "最新版本: 0.2.5.6-rc"）
        # 捕获组: 1=时间 2=名称 3=级别名 4=消息 5=第二分隔符 6=后续
        # (.+) 贪婪匹配到最后一个冒号，避免 (尝试次数: 1) 被提前分割
        # 使用 re.DOTALL 支持消息中包含换行符的日志（如窗口列表）
        m = re.match(
            r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^：]+)：(信息|警告|错误|严重错误)，(.+)([：:])(.*)$',
            raw_msg,
            re.DOTALL
        )

        if not m:
            # 无第二个分隔符：全部着色
            m = re.match(
                r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^：]+)：(信息|警告|错误|严重错误)，(.*)$',
                raw_msg,
                re.DOTALL
            )
            if not m:
                return raw_msg
            time_part = m.group(1)
            name_part = m.group(2)
            level_name = m.group(3)
            msg_content = m.group(4)
            sep2_char = ''
            after_part = ''
        else:
            time_part = m.group(1)
            name_part = m.group(2)
            level_name = m.group(3)
            msg_content = m.group(4)
            sep2_char = m.group(5)
            after_part = m.group(6)

        # 级别+内容合并（第一个：到第二个：之间）
        level_msg_part = level_name + '，' + msg_content
        level_color = LEVEL_COLORS.get(level_name, WHITE)

        # 时间 - 白色
        time_colored = f"{WHITE}{time_part}{RESET}"

        # 分隔符 " - " - 白色
        sep1 = f"{WHITE} - {RESET}"

        # logger名称 - 蓝色
        name_colored = f"{LOGGER_COLOR}{name_part}{RESET}"

        # 分隔符 "："（第一个） - 白色
        sep2 = f"{WHITE}：{RESET}"

        # 从第一个：到第二个：之间的内容（级别+逗号+消息）- 按级别着色
        colored_part = f"{level_color}{level_msg_part}{RESET}"

        if sep2_char:
            # 第二个分隔符 - 白色
            sep3 = f"{WHITE}{sep2_char}{RESET}"
            # 分隔符之后的内容 - 跟随级别颜色（信息保持白色，其他级别着色）
            after_color = level_color if level_name != '信息' else WHITE
            after_colored = f"{after_color}{after_part}{RESET}"
            return f"{time_colored}{sep1}{name_colored}{sep2}{colored_part}{sep3}{after_colored}"
        else:
            return f"{time_colored}{sep1}{name_colored}{sep2}{colored_part}"
