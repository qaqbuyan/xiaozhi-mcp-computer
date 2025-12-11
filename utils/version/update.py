import shutil
import logging
import threading
from ruamel.yaml import YAML
from handle.version import get_version
from mcp.server.fastmcp import FastMCP
from handle.path import get_config_path
from utils.file.download import download_file
from handle.install import install_requirements
from utils.version.requirements import get_new_requirements

logger = logging.getLogger('版本更新')

def update_client(mcp: FastMCP):
    @mcp.tool()
    def update_client() -> str:
        """用于下载最新的客户端版本
        如果当前版本未知，则必须调用‘ check_version ‘工具，获取最新版本信息，然后再调用该工具。
        当需要更新客户端版本信息时，立刻使用该工具下载最新版本。
        Notice：
            工具会自动下载最新的客户端版本文件，并将其配置文件复制到指定目录下，需要告诉告诉用户，该客户端跟配置文件的存储位置。
        """
        logger.info("进行客户端版本更新...")
        try:
            data = get_version()
            if not isinstance(data, dict):
                error = f"错误：get_version 返回的数据不是字典类型，而是 {type(data).__name__} 类型。"
                logger.error(error)
                return error
            if 'latest_version' in data and 'current_version' in data:
                if data['latest_version'] != data['current_version']:
                    if 'link' in data and data['link']:
                        logger.info(f"开始下载新版本 {data['latest_version']}")
                        result = download_file(data['link'])
                        if "文件下载成功" in result:
                            start_index = result.find("下载目录地址: ") + len("下载目录地址: ")
                            end_index = result.find("，文件名称:")
                            download_dir = result[start_index:end_index].strip()
                            try:
                                src_config = get_config_path()
                                dst_config = f"{download_dir}/config.yaml"
                                shutil.copy2(src_config, dst_config)
                                yaml = YAML()
                                yaml.preserve_quotes = True
                                with open(dst_config, 'r', encoding='utf-8') as f:
                                    config = yaml.load(f)
                                if 'latest_version' in data:
                                    config['version'] = data['latest_version']
                                with open(dst_config, 'w', encoding='utf-8') as f:
                                    yaml.dump(config, f)
                                # 比较依赖差异，只安装新增的依赖
                                new_requirements = ""
                                if 'current_requirements' in data and 'latest_requirements' in data:
                                    new_requirements = get_new_requirements(data['current_requirements'], data['latest_requirements'])
                                # 开启线程安装环境依赖（只安装新增的依赖）
                                if new_requirements:
                                    install_thread = threading.Thread(
                                        target=install_requirements, 
                                        args=(new_requirements,)
                                    )
                                    install_thread.daemon = True
                                    install_thread.start()
                                    msg = f"文件下载成功，成功复制并更新配置文件到 {download_dir} 目录下，正在后台安装新增的环境依赖: {new_requirements}..."
                                elif 'latest_requirements' in data and data['latest_requirements']:
                                    # 如果没有找到当前版本的依赖信息，则安装全部依赖
                                    install_thread = threading.Thread(
                                        target=install_requirements, 
                                        args=(data['latest_requirements'],)
                                    )
                                    install_thread.daemon = True
                                    install_thread.start()
                                    msg = f"文件下载成功，成功复制并更新配置文件到 {download_dir} 目录下，正在后台安装环境依赖..."
                                else:
                                    msg = f"文件下载成功，成功复制并更新配置文件到 {download_dir} 目录下"
                                logger.info(msg)
                                return msg
                            except Exception as e:
                                msg = f"文件下载成功，但是复制或更新配置文件时出错: {e}，请手动更新配置文件"
                                logger.error(msg)
                                return msg
                        return result
                    else:
                        msg = "错误：未找到新版本的下载链接。"
                        logger.error(msg)
                        return msg
                else:
                    msg = f"当前已是最新版本：{data['current_version']}"
                    logger.info(msg)
                    return msg
            else:
                error = "错误：未获取到有效的版本信息。"
                logger.error(error)
                return error
        except Exception as e:
            error = f"处理版本更新时出错: {e}"
            logger.error(error)
            return error