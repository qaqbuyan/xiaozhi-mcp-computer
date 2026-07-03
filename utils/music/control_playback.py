import logging
from mcp.server.fastmcp import FastMCP
from utils.music.play import playback_manager
from handle.missing_params import ask_on_missing

logger = logging.getLogger('音乐控制')

def computer_control_playback(mcp: FastMCP):
    @mcp.tool()
    @ask_on_missing('action')
    def computer_control_playback(action: int = 2) -> dict:
        """用于控制当前音乐的播放状态：继续播放、停止播放或暂停播放。
        当用户说"继续播放音乐"、"停止播放"、"暂停播放"或类似指令时，立刻使用该工具。

        重要说明：
        - 继续播放（action=1）：从暂停状态恢复播放。如果存在已保存的暂停队列，则按该队列继续播放；
            否则如果当前队列有歌曲，则继续播放当前队列。
        - 停止播放（action=2）：立即停止当前播放，并清空当前播放队列和暂停队列，后续无法继续播放。
            请明确告知用户：当前歌曲会继续播放至结束，但后续歌曲将不再播放。
        - 暂停播放（action=3）：立即停止当前播放，但将当前播放队列保存到内存中。
            请明确告知用户：当前歌曲会继续播放至结束，但已保存的队列可在"继续播放"时恢复。

        Args:
            action (int): 1 表示继续播放，2 表示停止播放，3 表示暂停播放。默认为 2。

        Returns:
            dict: 包含 success 和 result 的字典
        """
        try:
            playback_info = playback_manager.get_current_playback_info()
            is_playing = playback_info.get("is_playing", False)
            queue_length = playback_info.get("queue_length", 0)
            current_display_name = playback_info.get("current_display_name", "")

            # 暂停播放
            if action == 3:
                if not is_playing and queue_length == 0:
                    logger.info("当前没有正在播放的音乐，也没有待播放列表，无法暂停")
                    return {
                        "success": False,
                        "result": "当前没有正在播放的音乐，无法暂停"
                    }
                playback_manager.pause_playback()
                msg = "已暂停播放音乐"
                if current_display_name:
                    msg += f"，当前歌曲: {current_display_name} 已停止"
                msg += "，当前歌单已保存到内存，可随时继续播放"
                logger.info(msg)
                return {
                    "success": True,
                    "result": msg
                }

            # 继续播放
            if action == 1:
                if is_playing:
                    msg = "音乐已经在播放中"
                    if current_display_name:
                        msg += f"，当前正在播放: {current_display_name}"
                    logger.info(msg)
                    return {
                        "success": True,
                        "result": msg
                    }

                resumed = playback_manager.resume_playback()
                if resumed:
                    logger.info("已继续播放音乐")
                    return {
                        "success": True,
                        "result": "已继续播放音乐"
                    }
                else:
                    # 没有暂停队列，尝试播放当前队列
                    if queue_length > 0:
                        playback_manager.start_playback()
                        logger.info("已继续播放当前队列中的音乐")
                        return {
                            "success": True,
                            "result": "已继续播放当前队列中的音乐"
                        }
                    else:
                        logger.info("没有可继续播放的音乐")
                        return {
                            "success": False,
                            "result": "没有可继续播放的音乐，请先播放或暂停一个歌单"
                        }

            # 停止播放
            if action == 2:
                playback_manager.stop_current_playback()
                logger.info("已停止播放音乐")
                return {
                    "success": True,
                    "result": "已停止播放音乐"
                }

            # 未知 action
            logger.warning(f"未知的播放控制 action: {action}")
            return {
                "success": False,
                "result": f"未知的操作类型: {action}，请使用 1（继续）、2（停止）或 3（暂停）"
            }

        except Exception as e:
            error_msg = f"控制音乐播放时出错: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "result": error_msg
            }