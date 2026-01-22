"""
项目结构验证脚本
检查所有必要的文件和模块是否存在
"""

import os
import sys


def check_file(filepath, description):
    """检查文件是否存在"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {filepath}")
    return exists


def check_directory(dirpath, description):
    """检查目录是否存在"""
    exists = os.path.isdir(dirpath)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {dirpath}")
    return exists


def main():
    print("=" * 60)
    print("TicketMaster 项目结构验证")
    print("=" * 60)
    print()

    results = []

    # 检查根目录文件
    print("【根目录文件】")
    results.append(check_file("README.md", "使用文档"))
    results.append(check_file("QUICKSTART.md", "快速入门"))
    results.append(check_file("DEVELOPMENT.md", "开发文档"))
    results.append(check_file("LICENSE", "许可证"))
    results.append(check_file("requirements.txt", "依赖清单"))
    results.append(check_file("setup.py", "安装脚本"))
    results.append(check_file("build_exe.py", "打包脚本"))
    results.append(check_file("TicketMaster.spec", "PyInstaller 配置"))
    results.append(check_file("install.bat", "Windows 安装脚本"))
    results.append(check_file("run.bat", "Windows 运行脚本"))
    results.append(check_file("main.py", "程序入口"))
    print()

    # 检查目录
    print("【目录结构】")
    results.append(check_directory("gui", "GUI 模块"))
    results.append(check_directory("core", "核心模块"))
    results.append(check_directory("platforms", "平台模块"))
    results.append(check_directory("utils", "工具模块"))
    results.append(check_directory("models", "数据模型"))
    results.append(check_directory("icons", "图标资源"))
    print()

    # 检查 GUI 模块文件
    print("【GUI 模块】")
    results.append(check_file("gui/__init__.py", "GUI 初始化"))
    results.append(check_file("gui/main_window.py", "主窗口"))
    results.append(check_file("gui/accounts_widget.py", "账号管理界面"))
    results.append(check_file("gui/tasks_widget.py", "任务管理界面"))
    results.append(check_file("gui/logs_widget.py", "日志查看界面"))
    results.append(check_file("gui/settings_widget.py", "设置界面"))
    print()

    # 检查核心模块文件
    print("【核心模块】")
    results.append(check_file("core/__init__.py", "Core 初始化"))
    results.append(check_file("core/database.py", "数据库层"))
    results.append(check_file("core/logger.py", "日志系统"))
    results.append(check_file("core/scheduler.py", "任务调度器"))
    print()

    # 检查平台模块文件
    print("【平台模块】")
    results.append(check_file("platforms/__init__.py", "Platforms 初始化"))
    results.append(check_file("platforms/base_platform.py", "平台基类"))
    results.append(check_file("platforms/platform_12306.py", "12306 平台"))
    results.append(check_file("platforms/platform_damai.py", "大麦网平台"))
    results.append(check_file("platforms/platform_ctrip.py", "携程平台"))
    print()

    # 检查工具模块文件
    print("【工具模块】")
    results.append(check_file("utils/__init__.py", "Utils 初始化"))
    results.append(check_file("utils/encryption.py", "加密工具"))
    results.append(check_file("utils/proxy.py", "代理工具"))
    results.append(check_file("utils/config.py", "配置工具"))
    print()

    # 检查数据模型文件
    print("【数据模型】")
    results.append(check_file("models/__init__.py", "Models 初始化"))
    results.append(check_file("models/account.py", "账号模型"))
    results.append(check_file("models/task.py", "任务模型"))
    print()

    # 检查图标资源
    print("【图标资源】")
    results.append(check_file("icons/README.md", "图标说明"))
    print()

    # 统计结果
    print("=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"验证完成！")
    print(f"总计: {total}")
    print(f"通过: {passed} ✓")
    print(f"失败: {failed} ✗")
    print("=" * 60)

    if failed == 0:
        print("\n✓ 所有文件检查通过！项目结构完整。")
        return 0
    else:
        print(f"\n✗ 有 {failed} 个文件缺失，请检查项目结构。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
