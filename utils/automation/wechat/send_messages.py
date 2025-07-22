import os
import logging
from wxauto import WeChat
from mcp.server.fastmcp import FastMCP
from utils.is_process_running import is_process_running

logger = logging.getLogger('微信消息')

def send_wechat_messages_or_files(mcp: FastMCP):
    @mcp.tool()
    def send_wechat_messages_or_files(data: list) -> str:
        """发送微信消息，批量或单条发送文件以及文本消息，支持 html 的 emoji ，例如 ’😍’ 。
        当用户需要发送文件或者消息（内容）给某一个人时，立刻调用该工具，无需确认
        Notice：
            1.如果出现 ‘微信未运行，请先启动微信’ 则使用 ’scan_statistics’ 工具获取微信程序的位置
                找到了直接使用 ’open_program’ 工具打开
                如果打开成功了，必须询问用户是否同意登入微信
                需要就立刻使用 ’get_image_recognition_text’ 工具获取 ’进入微信’ 文字坐标
                获取到了就立刻使用 ’move_mouse_region’ 工具将鼠标指针移动到指定区域，
                然后立刻使用 ’click’ 工具点击鼠标左键

            2.如果是群聊天支持 ’@用户’ 以及换行，文本信息格式为 ’\n{@张三}’。
                例如：’各位下午好\n{@张三}负责xxx\n{@李四}负责xxxx’
        Args:
            data (list): 消息数据列表，每个元素为一个字典，包含消息内容和接收人列表，结构：
                [
                    {
                        "content": "C:/Users/Administrator/Desktop/QQ20250714-024436.png", // 文本消息 或者 文件的绝对路径
                        "list": [
                            "文件传输助手" // 单个接收人 或者 多个接收人 的名称
                            ...
                        ]
                    }
                    ...
                ]
        Returns:
            str: 发送消息的结果
        """
        logger.info('发送微信消息...')
        # 验证微信是否运行
        if not is_process_running('WeChat.exe'):
            msg = '微信未运行，请先启动微信。'
            logger.error(msg)
            return msg
        # 初始化微信实例
        wx = WeChat()
        msg = ''
        for item in data:
            content = item.get('content', '')
            logger.info(f'消息内容：{content}')
            user_list = item.get('list', [])
            is_file = os.path.exists(content)
            for user_info in user_list:
                if isinstance(user_info, dict):
                    user = next(iter(user_info.values()), '')
                elif isinstance(user_info, str):
                    user = user_info
                else:
                    continue
                if user and content:
                    if is_file:
                        response = wx.SendFiles(filepath=content, who=user)
                        msg += f"发送结果: {'发送成功' if response else '发送失败'}"
                        logger.info(msg)
                    else:
                        response = wx.SendMsg(content, who=user)
                        msg += f"发送结果: {'发送成功' if response is None else f'发送失败，返回内容: {response}'}"
                        logger.info(msg)
                else:
                    msg += f'消息发送失败，接收人：{user}'
                    logger.error(msg)
        return msg