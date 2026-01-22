"""
打包脚本
使用 PyInstaller 将 TicketMaster 打包为 Windows 可执行文件
"""

import os
import sys
import subprocess


def clean_build():
    """清理旧的构建文件"""
    print("清理旧的构建文件...")

    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            for root, dirs, files in os.walk(dir_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except:
                        pass

    print("清理完成。")


def build_exe():
    """构建 exe 文件"""
    print("开始构建 exe 文件...")

    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--clean',
        'TicketMaster.spec'
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✓ 构建成功！")
        print("\n可执行文件位置: dist/TicketMaster/TicketMaster.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 60)
    print("TicketMaster 打包脚本")
    print("=" * 60)
    print()

    # 确认清理
    print("步骤 1: 清理旧的构建文件")
    clean_build()
    print()

    # 构建exe
    print("步骤 2: 构建可执行文件")
    build_exe()
    print()

    print("=" * 60)
    print("打包完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
