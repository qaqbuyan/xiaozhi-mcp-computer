import logging
from wxauto import WeChat
from mcp.server.fastmcp import FastMCP
from utils.is_process_running import is_process_running

logger = logging.getLogger('微信消息')

def get_current_wechat_chat_window_message(mcp: FastMCP):
    @mcp.tool()
    def get_current_wechat_chat_window_message() -> str:
        """获取当前微信聊天窗口消息
        Notice：
            如果出现 ‘微信未运行，请先启动微信’ 则使用 ’scan_statistics’ 工具获取微信程序的位置
            找到了直接使用 ’open_program’ 工具打开
            如果打开成功了，必须询问用户是否同意登入微信
            需要就立刻使用 ’get_image_recognition_text’ 工具获取 ’进入微信’ 文字坐标
            获取到了就立刻使用 ’move_mouse_region’ 工具将鼠标指针移动到指定区域，
            然后立刻使用 ’click’ 工具点击鼠标左键
        Returns:
            str: 聊天窗口消息，Self 发送的消息
        """
        logger.info('获取当前微信聊天窗口消息...')
        # 验证微信是否运行
        if not is_process_running('WeChat.exe'):
            msg = '微信未运行，请先启动微信。'
            logger.error(msg)
            return msg
        # 初始化微信实例
        wx = WeChat()
        # 获取当前聊天窗口的所有消息
        msgs = wx.GetAllMessage()
        # 加载当前窗口更多聊天记录
        # msgs =wx.LoadMoreMessage()
        msg_list = []
        for msg in msgs:
            msg_list.append(f"{msg.sender}: {msg.content}")
        msg = '\n'.join(msg_list)
        logger.info(msg)
        return msg