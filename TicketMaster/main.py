"""
TicketMaster - Windows 抢票软件主程序入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui import MainWindow


def main():
    """主函数"""
    # 启用高 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("TicketMaster")
    app.setApplicationDisplayName("TicketMaster 抢票软件")
    app.setOrganizationName("TicketMaster")
    app.setOrganizationDomain("ticketmaster.com")

    # 设置应用样式
    app.setStyle("Fusion")

    # 设置默认字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 创建主窗口
    main_window = MainWindow()
    main_window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
