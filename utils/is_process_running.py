import psutil

def is_process_running(process_name):
    """
    判断指定名称的程序是否正在运行
    :param process_name: 程序名称
    :return: 如果程序正在运行返回 True，否则返回 False
    """
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False