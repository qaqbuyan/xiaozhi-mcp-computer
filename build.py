import os
import time
import random
import string
import subprocess
from PyInstaller.__main__ import run
from handle.loader import load_config

print('开始构建...')
# 读取 requirements.txt 文件内容
requirements_txt_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
if os.path.exists(requirements_txt_path):
    print('生成环境依赖...')
    with open(requirements_txt_path, 'r', encoding='utf-8') as f:
        requirements_content = f.read()
    # 生成 requirements.py 文件
    requirements_py_path = os.path.join(os.path.dirname(__file__), 'handle', 'requirements.py')
    with open(requirements_py_path, 'w', encoding='utf-8') as f:
        f.write(f'requirements = \'\'\'\n{requirements_content}\n\'\'\'')
    
    print('生成证书...')
    # 生成随机密码
    password_length = len("zcXmem5r2VB8epNJPm5FEVFrnJFUBm")
    all_characters = string.ascii_letters + string.digits
    random_password = ''.join(random.choice(all_characters) for i in range(password_length))
    # 生成自签名证书并导出为 PFX 文件
    pfx_path = os.path.join(os.path.dirname(__file__), 'QianAn_CodeSign.pfx')
    powershell_generate_cert_cmd = f"""
    $cert = New-SelfSignedCertificate -Subject "CN=Qian An, E=buyan@mail.qaqbuyan.com" -KeyUsage DigitalSignature -TextExtension @("2.5.29.37={{text}}1.3.6.1.5.5.7.3.3") -FriendlyName "Qian An Code Signing" -NotBefore (Get-Date) -NotAfter (Get-Date).AddYears(10) -CertStoreLocation "Cert:\\CurrentUser\\My"
    $password = ConvertTo-SecureString -String "{random_password}" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath "{pfx_path}" -Password $password
    """
    try:
        subprocess.run(['powershell', '-Command', powershell_generate_cert_cmd], check=True)
        print("自签名证书生成并导出成功")
    except subprocess.CalledProcessError as e:
        print(f"生成自签名证书时出错: {e}")

    print('构建项目...')
    # 清理旧的dist文件
    dist_path = os.path.join(os.path.dirname(__file__), 'dist')
    if os.path.exists(dist_path):
        try:
            for f in os.listdir(dist_path):
                if f.startswith('小智控制电脑'):
                    os.remove(os.path.join(dist_path, f))
        except Exception as e:
            print(f"清理旧文件时出错: {e}")
            time.sleep(2)  # 等待2秒再重试

    # 获取配置文件中的版本号
    config = load_config()
    version = config['version']
    # 提取版本号中的数字部分
    version_parts = version.split('-')[0].split('.')
    file_vers = tuple(map(int, version_parts[:3])) + (0,)
    # 提取版本类型
    version_type = version.split('-')[1] if '-' in version else 'Stable'

    # 生成 version_info.txt 文件
    version_info_content = f"""VSVersionInfo(
    ffi=FixedFileInfo(
        filevers={file_vers},
        prodvers={file_vers},
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
        [
        StringTable(
            '080404B0',
            [StringStruct('CompanyName', 'Buyan'),
            StringStruct('FileDescription', '一个免安装的小智AI控制电脑'),
            StringStruct('FileVersion', '{version}'),
            StringStruct('InternalName', '小智AI控制电脑'),
            StringStruct('LegalCopyright', 'Copyright © 2025 Buyan. All Rights Reserved.'),
            StringStruct('OriginalFilename', '小智AI控制电脑'),
            StringStruct('ProductName', '小智AI控制电脑'),
            StringStruct('ProductVersion', '{version_type}')
            ])
        ]), 
        VarFileInfo([VarStruct('Translation', [2052, 1200])])
    ]
    )"""

    version_info_path = os.path.join(os.path.dirname(__file__), 'version_info.txt')
    with open(version_info_path, 'w', encoding='utf-8') as f:
        f.write(version_info_content)

    params = [
        # 修改为动态版本号
        f'--name=小智控制电脑 V{version}',
        '--onefile',
        '--icon=favicon.ico',
        '--distpath=dist',
        '--workpath=build',
        '--add-data=mcp_pipe.py;.',
        '--add-data=aggregate.py;.',
        '--add-data=config.yaml;.',
        '--add-data=services;services',
        '--add-data=handle;handle',
        '--add-data=utils;utils',
        '--add-data=favicon.ico;.',
        '--hidden-import=services.register',
        '--hidden-import=utils.open.program',
        '--hidden-import=websockets',
        '--hidden-import=websockets.client',
        '--hidden-import=websockets.server',
        '--hidden-import=mcp.server.fastmcp',
        '--hidden-import=ctypes',
        '--hidden-import=yaml',
        '--hidden-import=asyncio',
        '--hidden-import=logging.handlers',
        '--hidden-import=subprocess',
        '--hidden-import=multiprocessing',
        '--hidden-import=multiprocessing.spawn',
        '--hidden-import=tkinter',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=pyperclip',
        '--version-file=version_info.txt',
        'exec_wrapper.py'
    ]

    print('打包项目...')
    # 先执行打包操作
    run(params)

    print('签名项目...')
    # 对打包后的可执行文件进行签名
    exe_path = os.path.join(dist_path, f'小智控制电脑 V{version}.exe')
    # 使用新生成的证书路径
    pfx_path = os.path.join(os.path.dirname(__file__), 'QianAn_CodeSign.pfx')

    print(f"尝试查找的可执行文件路径: {exe_path}")
    print(f"尝试查找的 PFX 文件路径: {pfx_path}")

    max_attempts = 10
    attempt = 0
    while attempt < max_attempts:
        try:
            # 尝试以写入模式打开文件，检查文件是否被占用
            with open(exe_path, 'a'):
                print(f"文件 {exe_path} 已可访问，准备进行签名")
                break
        except Exception as e:
            print(f"文件 {exe_path} 仍被占用，等待 5 秒后重试 ({attempt + 1}/{max_attempts})")
            time.sleep(5)
            attempt += 1

    if attempt == max_attempts:
        print(f"无法访问文件 {exe_path}，已达到最大重试次数。尝试终止可能占用文件的进程（需手动操作）")
    else:
        print('开始签名...')
        if os.path.exists(exe_path) and os.path.exists(pfx_path):
            try:
                # 使用随机密码进行签名
                powershell_cmd = f"""
                $pfxPassword = ConvertTo-SecureString -String "{random_password}" -Force -AsPlainText
                $pfx = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2("{pfx_path}", $pfxPassword)
                $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "CurrentUser")
                $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
                $store.Add($pfx)
                $store.Close()
                $cert = Get-ChildItem -Path Cert:\\CurrentUser\\My | Where-Object {{$_.Thumbprint -eq $pfx.Thumbprint}}
                Set-AuthenticodeSignature -FilePath "{exe_path}" -Certificate $cert -TimestampServer "http://timestamp.digicert.com" -HashAlgorithm "SHA256"
                """
                subprocess.run(['powershell', '-Command', powershell_cmd], check=True)
                print("数字签名添加成功")
            except subprocess.CalledProcessError as e:
                print(f"数字签名添加失败: {e}")
        else:
            print("可执行文件或 PFX 文件不存在")
else:
    print('requirements.txt 文件不存在')