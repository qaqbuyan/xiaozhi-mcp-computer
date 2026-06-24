import sys
import time
import logging
from handle.ws_connection import set_mcp_script, connect_with_retry

async def main(config, logger, args=None, on_process_end=None):
    """管道服务主入口函数"""
    try:
        if args is None:
            args = sys.argv[1:]
        if not args:
            logger.error("请指定要运行的管道服务代理路径")
            time.sleep(30)
            return 1
        set_mcp_script(args[0])
        logger.info("准备运行管道服务...")
        if not config.get('endpoint') or not isinstance(config['endpoint'], dict):
            logger.error("请确认配置，该配置是无效的")
            time.sleep(30)
            return 1
        endpoint_url = config['endpoint'].get('url', '')
        if not endpoint_url.startswith(('wss://', 'ws://')):
            logger.error("请确认配置，WebSocket端点URL必须以wss://或ws://开头")
            time.sleep(30)
            return 1
        return await connect_with_retry(config['endpoint']['url'])
    except Exception as e:
        from handle.ws_utils import translate_ws_error
        logger.error(f"管道服务启动失败: {translate_ws_error(e)}")
        time.sleep(30)
        return 1