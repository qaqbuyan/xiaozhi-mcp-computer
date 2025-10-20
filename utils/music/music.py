import os
import json
import logging
import requests
from handle.loader import load_config
from datetime import datetime, timedelta

logger = logging.getLogger('音乐信息')

class MusicPlayer:
    def __init__(self):
        config = load_config()
        
        # 验证并设置音乐API地址
        music_api = config['utils']['music']['music_api']
        if not music_api.startswith(('http://', 'https://')):
            raise ValueError(f"无效的音乐API地址: {music_api}，必须以http://或https://开头")
        self.music_api = music_api
        
        # 设置音乐音质类型
        self.song_type = config['utils']['music']['song_type']
        
        # 设置请求头
        self.headers = {
            "User-Agent": config['utils']['music']['headers']['User-Agent']
        }
    
    def get_music_name_info(self, song_name, singer_name=""):
        """获取音乐名称和歌手信息
        
        Args:
            song_name (str): 歌曲名称，禁止为空
            singer_name (str): 歌手名称，可以为空
            
        Returns:
            dict: 包含success和result两个键的字典
        """
        logger.info("获取音乐信息")
        if not song_name:
            return {
                "success": False,
                "result": "歌曲名称不能为空"
            }
        logger.info(f"歌曲名称: {song_name}")
        logger.info(f"歌手名称: {singer_name if singer_name else '不限制歌手'}")
        try:
            # 构建请求URL
            url = f"{self.music_api}?songname&name={song_name}"
            if singer_name:
                url += f"&singer={singer_name}"
            
            # 发送HTTP请求
            logger.info(f"正在获取歌曲信息")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # 返回响应内容
            logger.info(f"获取歌曲信息成功")
            return {
                "success": True,
                "result": response.text
            }
        except Exception as e:
            msg = f"获取歌曲信息失败: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
    
    def get_music_mid_info(self, mid):
        """获取音乐mid信息
        
        Args:
            mid (str): 音乐的mid值
            
        Returns:
            dict: 包含success和result两个键的字典
        """
        logger.info("获取音乐mid信息")
        if not mid:
            msg = "mid值不能为空"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        try:
            # 构建请求URL
            url = f"{self.music_api}?songmid&mid={mid}"
            
            # 发送HTTP请求
            logger.info(f"正在获取歌曲mid信息")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            logger.info(f"获取歌曲mid信息成功")
            # 返回响应内容
            return {
                "success": True,
                "result": response.text
            }
        except Exception as e:
            msg = f"获取歌曲mid信息失败: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
    
    def get_download_link(self, music_json: str) -> dict:
        """获取下载链接
        
        Args:
            music_json (str): 音乐信息的JSON字符串
            
        Returns:
            dict: 包含成功状态和结果消息的字典
                {"success": bool, "result": str}
        """
        logger.info("获取下载链接")
        try:
            # 解析JSON
            data = json.loads(music_json)
            
            # 判断JSON格式类型
            logger.info("音源分类")
            # 格式1: 缓存仓库 格式
            if "code" in data and "message" in data:
                logger.info("使用 缓存仓库")
                # 检查响应是否成功
                if data.get("code") != 200:
                    msg = f"错误：API返回非成功状态码 {data.get('code', '未知')}"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                if "message" not in data:
                    msg = "错误：响应数据中缺少message字段"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                # 从message中获取歌曲信息
                message = data["message"]
                
                # 获取类型信息
                type_info = message.get("type", {})
                if not type_info:
                    msg = "错误：未找到任何音质类型信息"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                # 获取指定song_type的信息，如果不存在则取第一个可用的
                bitrate_info = None
                if self.song_type in type_info:
                    bitrate_info = type_info[self.song_type]
                else:
                    # 如果没有找到指定的类型，取第一个可用的
                    first_key = next(iter(type_info))
                    bitrate_info = type_info[first_key]
                    msg = f"警告：未找到指定的音质类型 {self.song_type}，将使用第一个可用类型 {first_key}"
                    logger.warning(msg)
                
                if not bitrate_info:
                    msg = f"错误：未找到音质详细信息 {self.song_type}"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                # 获取文件后缀和比特率
                suffix = bitrate_info.get("suffix", "")
                if not suffix:
                    msg = "错误：未找到文件后缀"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                bitrate = bitrate_info.get("bitrate", "")
                if not bitrate:
                    msg = f"错误：未找到比特率信息 '{bitrate}'"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                # 检查必要的歌曲信息
                song_id = message.get("id", "")
                if not song_id:
                    msg = f"错误：未找到歌曲ID {song_id}"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                song_mid = message.get("mid", "")
                if not song_mid:
                    msg = f"错误：未找到歌曲MID {song_mid}"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                song_name = message.get("name", "").replace('-', ' ')
                if not song_name:
                    msg = f"错误：未找到歌曲名称 {song_name}"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                singers = message.get("singer", [])
                if not singers:
                    msg = f"警告：未找到歌手信息 {song_name}"
                    logger.warning(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                if isinstance(singers, list):
                    singer_names = ", ".join(singers)
                else:
                    singer_names = str(singers)
                
                album_name = message.get("album", "").replace('-', ' ')
                if not album_name:
                    album_name = ""
                
                interval = message.get("interval", "").replace(':', '_')
                if not interval:
                    msg = f"警告：未找到歌曲时长信息 {interval}"
                    logger.warning(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                # 构建链接参数部分，格式：&不为谁而作的歌 (Live)-谁是大歌神 第3期-林俊杰, 张梦羽-002VSBjz3gZNve-105725590-4_35
                link_params = f"music/&{song_name}-{album_name}-{singer_names}-{song_mid}-{song_id}-{interval}"
                
                # 完整下载链接，使用从JSON中获取的后缀和比特率
                download_link = f"{self.music_api}{link_params}/{self.song_type}-{bitrate}.{suffix}"
                return {
                    "success": True,
                    "result": download_link
                }
            # 格式2: 在线音乐 格式
            elif "music_url" in data:
                logger.info("使用 在线音乐")
                music_urls = data.get("music_url", {})
                if not music_urls:
                    msg = "错误：未找到music_url字段或其为空"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                # 获取指定song_type的URL，如果不存在则取第一个可用的
                target_url_info = None
                if self.song_type in music_urls:
                    target_url_info = music_urls[self.song_type]
                else:
                    # 如果没有找到指定的类型，取第一个可用的
                    first_key = next(iter(music_urls))
                    target_url_info = music_urls[first_key]
                    msg = f"警告：未找到指定的音质类型 {self.song_type}，将使用第一个可用类型 {first_key}"
                    logger.warning(msg)
                
                if not target_url_info or "url" not in target_url_info:
                    msg = "错误：未找到有效下载链接"
                    logger.error(msg)
                    return {
                        "success": False,
                        "result": msg
                    }
                
                download_link = target_url_info["url"]
                logger.info("成功从music_url获取下载链接")
                return {
                    "success": True,
                    "result": download_link
                }
            else:
                msg = "错误：音源类型分类"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
        except json.JSONDecodeError as e:
            msg = f"错误：JSON解析失败 - {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        except Exception as e:
            msg = f"错误：获取下载链接失败 - {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
    
    def get_music_extension(self, download_link: str) -> str:
        """从下载链接中获取文件后缀名并验证是否为有效的音频格式
        
        Args:
            download_link (str): 下载链接
            
        Returns:
            str: 有效的文件后缀名（如'.mp3'），如果无效则返回空字符串
        """
        # 有效的音频格式列表
        valid_audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
        
        # 首先尝试常规方法提取后缀名
        music_extension = os.path.splitext(download_link)[1].lower()
        
        # 检查是否获取到了有效的后缀名
        if music_extension and music_extension in valid_audio_extensions:
            return music_extension
        
        # 如果常规方法失败，尝试从URL中匹配特定模式提取后缀名
        # 匹配 j. 到 ?guid= 之间的部分作为后缀名
        try:
            # 查找 '.xxx?guid=' 这样的模式
            start_index = download_link.rfind('.')
            if start_index != -1:
                # 查找 ?guid= 的位置
                end_index = download_link.find('?guid=', start_index)
                if end_index != -1:
                    # 提取 .xxx 部分
                    potential_extension = download_link[start_index:end_index].lower()
                    if potential_extension in valid_audio_extensions:
                        return potential_extension
            
            # 如果没找到 ?guid=，尝试查找其他查询参数分隔符 ?
            start_index = download_link.rfind('.')
            if start_index != -1:
                end_index = download_link.find('?', start_index)
                if end_index != -1:
                    potential_extension = download_link[start_index:end_index].lower()
                    if potential_extension in valid_audio_extensions:
                        return potential_extension
        except Exception as e:
            msg = f"提取后缀名时出错: {str(e)}"
            logger.error(msg)
        
        # 如果所有方法都失败，返回空字符串
        return ""
    
    def get_song_list(self, tid: int) -> dict:
        """获取歌单中的所有歌曲信息
        
        Args:
            tid (int): 歌单的tid值
            
        Returns:
            dict: 包含success和result两个键的字典，result为歌曲信息列表
        """
        logger.info(f"开始获取歌单 {tid} 中的所有歌曲信息")
        if not tid:
            msg = "歌单tid不能为空"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        # 缓存文件路径
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{tid}.json")
        
        # 检查缓存文件是否存在且在30分钟内
        if os.path.exists(cache_file):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mtime < timedelta(minutes=30):
                try:
                    # 读取缓存文件
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    # 验证缓存数据的有效性
                    if isinstance(cached_data, dict) and "song_list" in cached_data:
                        song_list = cached_data["song_list"]
                        if isinstance(song_list, list) and song_list:
                            msg = f"使用缓存获取歌单 {tid}，共{len(song_list)}首歌曲"
                            logger.info(msg)
                            return {
                                "success": True,
                                "result": song_list,
                                "cached": True
                            }
                except Exception as e:
                    logger.warning(f"读取缓存文件失败，将重新请求: {str(e)}")
        
        try:
            # 发送HTTP请求
            response = requests.get(self.music_api + "?songlist&tid=" + str(tid), headers=self.headers)
            response.raise_for_status()  # 检查请求是否成功
            
            # 解析JSON响应
            data = response.json()
            
            # 提取所有歌曲信息
            song_list = []
            if "message" in data and "playlists" in data["message"]:
                for song in data["message"]["playlists"]:
                    if "mid" in song:
                        # 提取歌手信息
                        singers = []
                        if "singer" in song and isinstance(song["singer"], list):
                            for singer in song["singer"]:
                                if "name" in singer:
                                    singers.append(singer["name"])
                        
                        song_info = {
                            "mid": song["mid"],
                            "name": song.get("name", ""),
                            "singers": singers,
                            "singer_names": ", ".join(singers) if singers else "未知歌手"
                        }
                        song_list.append(song_info)
            
            # 保存到缓存文件
            try:
                cache_data = {
                    "tid": tid,
                    "timestamp": datetime.now().isoformat(),
                    "song_list": song_list
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                logger.info(f"歌单 {tid} 数据已缓存到: {cache_file}")
            except Exception as e:
                logger.warning(f"保存缓存文件失败: {str(e)}")
            
            msg = f"从API获取歌单 {tid}，共{len(song_list)}首歌曲"
            logger.info(msg)
            return {
                "success": True,
                "result": song_list,
                "cached": False
            }
            
        except Exception as e:
            msg = f"获取歌单 {tid} 失败: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }

    def get_new_songs(self, type=1):
        """获取新歌速递中的歌曲信息
        
        Args:
            type (int): 新歌类型，0表示新发布的歌曲
                        1表示内地，2表示欧美，3表示日本，4表示韩国，6表示港台
        Returns:
            dict: 包含success和result两个键的字典，result为包含mid和歌手信息的列表
        """
        msg = f"开始获取新歌速递，类型: {type}"
        logger.info(msg)
        try:
            # 发送HTTP请求
            response = requests.get(f"{self.music_api}?newsongs&type={type}", headers=self.headers)
            response.raise_for_status()  # 检查请求是否成功
            
            # 解析JSON响应
            data = response.json()
            
            # 提取歌曲信息（mid和歌手）
            song_info_list = []
            if "code" in data and data["code"] == 200 and "message" in data and "playlists" in data["message"]:
                for song in data["message"]["playlists"]:
                    if "mid" in song:
                        # 提取歌手信息，多个歌手使用"/"连接
                        singer_names = []
                        if "singer" in song and isinstance(song["singer"], list):
                            for singer in song["singer"]:
                                if "name" in singer:
                                    singer_names.append(singer["name"])
                        
                        # 将歌手信息连接成字符串
                        singer_str = "/".join(singer_names) if singer_names else "未知歌手"
                        
                        # 添加歌曲信息到列表
                        song_info_list.append({
                            "mid": song["mid"],
                            "singer": singer_str
                        })
            
            msg = f"从新歌速递中获取到 {len(song_info_list)} 首歌曲信息"
            logger.info(msg)
            return {
                "success": True,
                "result": song_info_list
            }
            
        except Exception as e:
            msg = f"获取新歌速递失败: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
    
    def download_music(self, download_link):
        """下载音乐文件到tmp文件夹
        
        Args:
            download_link (str): 音乐下载链接
            
        Returns:
            dict: 包含success和result两个键的字典
        """
        logger.info("下载音乐")
        if not download_link:
            msg = "错误：下载链接为空"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        
        try:
            # 创建运行目录下的tmp文件夹（如果不存在）
            # 获取当前工作目录（运行目录）
            current_working_dir = os.getcwd()
            tmp_dir = os.path.join(current_working_dir, "tmp")
            os.makedirs(tmp_dir, exist_ok=True)
            
            # 获取文件后缀名并验证
            file_extension = self.get_music_extension(download_link)
            if not file_extension:
                msg = "错误：无法从下载链接中获取有效的文件后缀名"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
            
            # 定义文件路径，使用动态后缀名
            file_path = os.path.join(tmp_dir, f"music{file_extension}")
            
            # 删除所有可能的音频格式文件
            valid_audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
            for ext in valid_audio_extensions:
                possible_file = os.path.join(tmp_dir, f"music{ext}")
                if os.path.exists(possible_file):
                    os.remove(possible_file)
                    msg = f"已删除旧的音频文件: {possible_file}"
                    logger.info(msg)
            
            # 下载文件
            msg = f"正在下载音乐文件到: {file_path}"
            logger.info(msg)
            response = requests.get(download_link, headers=self.headers, stream=True)
            
            # 检查响应是否成功
            if response.status_code != 200:
                msg = f"下载请求失败，状态码: {response.status_code}"
                logger.error(msg)
                return {
                    "success": False,
                    "result": msg
                }
            
            # 验证内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type or not ('audio' in content_type or 'octet-stream' in content_type):
                msg = f"警告：响应内容类型不是预期的音频文件，而是: {content_type}"
                logger.warning(msg)
            
            # 保存文件
            msg = f"开始保存音乐文件到: {file_path}"
            logger.info(msg)
            # 文件大小
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                msg = "警告：下载的文件大小为0字节"
                logger.warning(msg)
                return {
                    "success": False,
                    "result": msg
                }
            
            downloaded_size = 0
            
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # 可选：打印下载进度
                        # if total_size > 0:
                        #     progress = downloaded_size / total_size * 100
                        #     logger.info(f"下载进度: {progress:.2f}%")
            
            msg = f"音乐文件下载完成，文件大小: {os.path.getsize(file_path)} 字节"
            logger.info(msg)
            return {
                "success": True,
                "result": f"音乐已成功下载到: {file_path}"
            }
        except requests.exceptions.RequestException as e:
            msg = f"网络请求异常: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        except IOError as e:
            msg = f"文件操作异常: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
        except Exception as e:
            msg = f"下载音乐时发生未知错误: {str(e)}"
            logger.error(msg)
            return {
                "success": False,
                "result": msg
            }
    
    def process_music_info(self, music_info_result):
        """处理音乐信息并下载音乐（不播放）
        
        Args:
            music_info_result: 包含音乐信息的结果对象
            
        Returns:
            dict: 包含操作结果的字典，格式为: 
                { 
                    "success": bool,  # 是否成功 
                    "result": str,    # 结果消息 
                    "file_path": str, # 下载的音乐文件路径
                    "duration": str,  # 音乐时长
                    "song_name": str, # 歌曲名称
                    "singer_name": str, # 歌手名称（多个歌手使用/连接）
                    "album_name": str  # 专辑名称
                }
        """
        logger.info("处理音乐信息并下载音乐")
        # 获取下载链接
        link_result = self.get_download_link(music_info_result["result"])
        
        # 验证下载链接是否正常获取
        if not link_result or not link_result.get("success", False):
            error_msg = link_result.get('result', '未知错误') if link_result else '未知错误'
            return {
                "success": False,
                "result": f"无法获取下载链接: {error_msg}",
                "file_path": "",
                "duration": "",
                "song_name": "",
                "singer_name": "",
                "album_name": ""
            }
        
        # 下载音乐
        download_result = self.download_music(link_result["result"])
        
        # 验证下载是否成功
        if not download_result or not download_result.get("success", False):
            error_msg = download_result.get('result', '') if download_result else '未知错误'
            return {
                "success": False,
                "result": f"音乐下载失败: {error_msg}",
                "file_path": "",
                "duration": "",
                "song_name": "",
                "singer_name": "",
                "album_name": ""
            }
        
        # 获取下载的文件路径
        try:
            # 创建运行目录下的tmp文件夹路径
            current_working_dir = os.getcwd()
            tmp_dir = os.path.join(current_working_dir, "tmp")
            file_extension = self.get_music_extension(link_result["result"])
            file_path = os.path.join(tmp_dir, f"music{file_extension}")
            
            # 先将music_info_result["result"]解析为字典
            music_data = json.loads(music_info_result["result"])
            # 根据不同的格式进行处理
            # 缓存仓库 格式
            song_name = ""  # 歌曲名称
            singer_name = ""  # 歌手名称
            album_name = ""  # 专辑名称
            duration = ""
            
            if "code" in music_data and "message" in music_data:
                duration = music_data.get("message", {}).get("interval", "")
                song_name = music_data.get("message", {}).get("name", "")
                album_name = music_data.get("message", {}).get("album", "")
                # 处理歌手信息
                singers = music_data.get("message", {}).get("singer", "")
                if singers and isinstance(singers, list):
                    # 如果是歌手列表
                    # 检查列表元素是字典还是字符串
                    if singers and isinstance(singers[0], dict):
                        # 如果列表元素是字典，获取name字段
                        singer_name = "/".join([s.get("name", "") for s in singers if isinstance(s, dict) and s.get("name")])
                    else:
                        # 如果列表元素是字符串，直接连接
                        singer_name = "/".join([str(s) for s in singers if s])
                elif isinstance(singers, str):
                    # 如果是字符串，直接使用
                    singer_name = singers
            # 在线音乐 格式
            elif "music_info" in music_data:
                duration = music_data.get("music_info", {}).get("interval", "")
                song_name = music_data.get("music_info", {}).get("name", "")
                album_name = music_data.get("music_info", {}).get("album", "")
                # 处理歌手信息
                singers = music_data.get("music_info", {}).get("singer", "")
                if singers:
                    # 如果歌手信息是字符串，直接使用
                    if isinstance(singers, str):
                        # 将逗号分隔的歌手名转换为/连接
                        singer_name = singers.replace(", ", "/")
                    elif isinstance(singers, list):
                        # 如果是歌手列表
                        if singers and isinstance(singers[0], dict):
                            # 如果列表元素是字典，获取name字段
                            singer_name = "/".join([s.get("name", "") for s in singers if isinstance(s, dict) and s.get("name")])
                        else:
                            # 如果列表元素是字符串，直接连接
                            singer_name = "/".join([str(s) for s in singers if s])
                    else:
                        singer_name = str(singers)
            # 默认情况
            else:
                # 其他情况，默认值为空
                pass
            
            # 修改这一行，当专辑名称为空时设置为"无专辑"
            if not album_name or album_name.strip() == "":
                album_name = "无专辑"
                
            return {
                "success": True,
                "result": "音乐下载成功",
                "file_path": file_path,
                "duration": duration,
                "song_name": song_name,
                "singer_name": singer_name,
                "album_name": album_name
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "result": f"音乐下载成功，但解析音乐信息失败: {music_info_result.get('result', '')}",
                "file_path": "",
                "duration": "",
                "song_name": "",
                "singer_name": "",
                "album_name": ""
            }