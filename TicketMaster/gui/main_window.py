"""
主窗口模块
实现应用程序的主窗口，包含菜单栏、工具栏、状态栏和多标签页
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMenuBar, QMenu, QToolBar, QStatusBar, QAction, QStyle,
    QMessageBox, QApplication, QSystemTrayIcon, QMenu as TrayMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QCloseEvent

from core import Database, Logger, TaskScheduler
from models import Account, Task, PlatformType, TaskStatus
from platforms import Platform12306, PlatformDamai, PlatformCtrip
from utils import get_config, get_encryption
from gui.accounts_widget import AccountsWidget
from gui.tasks_widget import TasksWidget
from gui.logs_widget import LogsWidget
from gui.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    """主窗口类"""

    # 信号定义
    log_signal = pyqtSignal(str, str)  # level, message

    def __init__(self):
        super().__init__()

        # 初始化核心组件
        self.db = Database()
        self.logger = Logger(db=self.db)
        self.config = get_config()
        self.encryption = get_encryption()

        # 初始化调度器
        self.scheduler = TaskScheduler(db=self.db, logger=self.logger)

        # 平台实例字典
        self.platforms = {
            PlatformType.TICKET_12306: Platform12306(),
            PlatformType.DAMAI: PlatformDamai(),
            PlatformType.CTRIP: PlatformCtrip()
        }

        # 初始化 UI
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.init_tray()

        # 加载任务到调度器
        self.scheduler.load_tasks_from_db(self.execute_task)

        # 启动调度器
        self.scheduler.start()

        # 连接日志信号
        self.log_signal.connect(self._on_log)

        # 记录启动日志
        self.logger.info("应用程序已启动")

        # 定时更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 每5秒更新一次

    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle(f"TicketMaster v{self.config.get('version', '1.0.0')}")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(False)
        main_layout.addWidget(self.tab_widget)

        # 添加各个标签页
        self.accounts_widget = AccountsWidget(self.db, self.logger, self.encryption, self.platforms)
        self.tasks_widget = TasksWidget(self.db, self.logger, self.platforms, self.scheduler)
        self.logs_widget = LogsWidget(self.db, self.logger)
        self.settings_widget = SettingsWidget(self.config, self.logger)

        # 设置标签页样式
        self.tab_widget.addTab(self.accounts_widget, "👤 账号管理")
        self.tab_widget.addTab(self.tasks_widget, "🎫 抢票任务")
        self.tab_widget.addTab(self.logs_widget, "📋 日志查看")
        self.tab_widget.addTab(self.settings_widget, "⚙️ 系统设置")

        # 应用样式
        self.apply_style()

    def init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        # 导出配置
        export_config_action = QAction("导出配置", self)
        export_config_action.triggered.connect(self.export_config)
        file_menu.addAction(export_config_action)

        # 导入配置
        import_config_action = QAction("导入配置", self)
        import_config_action.triggered.connect(self.import_config)
        file_menu.addAction(import_config_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        # 清理日志
        clear_logs_action = QAction("清理日志", self)
        clear_logs_action.triggered.connect(self.clear_old_logs)
        tools_menu.addAction(clear_logs_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 刷新账号
        refresh_accounts_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "刷新账号", self
        )
        refresh_accounts_action.triggered.connect(self.accounts_widget.load_accounts)
        toolbar.addAction(refresh_accounts_action)

        toolbar.addSeparator()

        # 刷新任务
        refresh_tasks_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "刷新任务", self
        )
        refresh_tasks_action.triggered.connect(self.tasks_widget.load_tasks)
        toolbar.addAction(refresh_tasks_action)

        toolbar.addSeparator()

        # 启动调度器
        start_scheduler_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay),
            "启动调度", self
        )
        start_scheduler_action.triggered.connect(self.start_scheduler)
        toolbar.addAction(start_scheduler_action)

        # 停止调度器
        stop_scheduler_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop),
            "停止调度", self
        )
        stop_scheduler_action.triggered.connect(self.stop_scheduler)
        toolbar.addAction(stop_scheduler_action)

        toolbar.addSeparator()

        # 刷新日志
        refresh_logs_action = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "刷新日志", self
        )
        refresh_logs_action.triggered.connect(self.logs_widget.load_logs)
        toolbar.addAction(refresh_logs_action)

    def init_statusbar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)

        # 调度器状态
        self.scheduler_status_label = QLabel("调度器: 运行中" if self.scheduler.is_running() else "调度器: 已停止")
        self.status_bar.addPermanentWidget(self.scheduler_status_label)

        # 账号数量
        account_count = len(self.db.get_all_accounts())
        self.account_count_label = QLabel(f"账号: {account_count}")
        self.status_bar.addPermanentWidget(self.account_count_label)

        # 任务数量
        task_count = len(self.db.get_all_tasks())
        self.task_count_label = QLabel(f"任务: {task_count}")
        self.status_bar.addPermanentWidget(self.task_count_label)

    def init_tray(self):
        """初始化系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)

        # 设置托盘图标
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)

        # 创建托盘菜单
        tray_menu = TrayMenu(self)

        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 点击托盘图标显示/隐藏窗口
        self.tray_icon.activated.connect(self.on_tray_activated)

        # 显示托盘图标
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def apply_style(self):
        """应用样式"""
        style = """
            QMainWindow {
                background-color: #f5f5f5;
            }

            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }

            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }

            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0;
            }

            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0056b3;
            }

            QPushButton:pressed {
                background-color: #004494;
            }

            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }

            QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus {
                border: 2px solid #007bff;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #cccccc;
                gridline-color: #e0e0e0;
            }

            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }

            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """
        self.setStyleSheet(style)

    def update_status(self):
        """更新状态栏"""
        # 更新调度器状态
        if self.scheduler.is_running():
            self.scheduler_status_label.setText("调度器: 运行中")
            self.scheduler_status_label.setStyleSheet("color: green;")
        else:
            self.scheduler_status_label.setText("调度器: 已停止")
            self.scheduler_status_label.setStyleSheet("color: red;")

        # 更新账号数量
        account_count = len(self.db.get_all_accounts())
        self.account_count_label.setText(f"账号: {account_count}")

        # 更新任务数量
        task_count = len(self.db.get_all_tasks())
        running_count = len(self.db.get_tasks_by_status(TaskStatus.RUNNING))
        self.task_count_label.setText(f"任务: {task_count} (运行中: {running_count})")

    def start_scheduler(self):
        """启动调度器"""
        self.scheduler.start()
        self.logger.info("调度器已启动")
        self.update_status()

    def stop_scheduler(self):
        """停止调度器"""
        self.scheduler.stop()
        self.logger.info("调度器已停止")
        self.update_status()

    def execute_task(self, task: Task) -> dict:
        """
        执行任务（在后台线程中调用）

        Args:
            task: 任务对象

        Returns:
            执行结果字典
        """
        try:
            self.logger.info(f"开始执行任务: {task.name}", task_id=task.id)

            # 获取任务参数
            params = task.get_params()
            platform = self.platforms.get(task.platform)

            if not platform:
                raise Exception(f"不支持的平台: {task.platform}")

            # 获取关联的账号
            accounts = []
            for account_id in task.account_ids:
                account = self.db.get_account(account_id)
                if account and account.is_available():
                    accounts.append(account)

            if not accounts:
                raise Exception("没有可用的账号")

            # 使用第一个账号登录
            account = accounts[0]
            self.logger.info(f"使用账号登录: {account.username}", task_id=task.id)

            if not platform.login(account):
                raise Exception("登录失败")

            # 搜索票务
            search_params = params.get('search', {})
            tickets = platform.search(search_params)

            if not tickets:
                raise Exception("未找到相关票务信息")

            # 查找可用的票
            available_ticket = None
            for ticket in tickets:
                if ticket.is_available():
                    available_ticket = ticket
                    break

            if not available_ticket:
                raise Exception("暂无可用票")

            self.logger.info(f"找到可用票: {available_ticket.name}", task_id=task.id)

            # 下单
            order_params = params.get('order', {})
            order_result = platform.order(available_ticket.id, order_params)

            if order_result.success:
                self.logger.success(
                    f"抢票成功! 订单号: {order_result.order_id}",
                    task_id=task.id,
                    account_id=account.id,
                    platform=task.platform.value
                )
                return {
                    'success': True,
                    'order_id': order_result.order_id,
                    'message': order_result.message
                }
            else:
                raise Exception(order_result.error)

        except Exception as e:
            self.logger.error(
                f"任务执行失败: {str(e)}",
                task_id=task.id,
                exception=e
            )
            return {
                'success': False,
                'error': str(e)
            }

    def _on_log(self, level: str, message: str):
        """处理日志信号"""
        # 可以在这里更新日志显示
        pass

    def export_config(self):
        """导出配置"""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出配置",
            "config.json",
            "JSON Files (*.json)"
        )

        if filepath:
            try:
                self.config.export(filepath)
                QMessageBox.information(self, "成功", "配置导出成功！")
                self.logger.info(f"配置已导出到: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置失败: {str(e)}")
                self.logger.error(f"导出配置失败: {str(e)}")

    def import_config(self):
        """导入配置"""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "导入配置",
            "",
            "JSON Files (*.json)"
        )

        if filepath:
            try:
                self.config.import_config(filepath)
                QMessageBox.information(self, "成功", "配置导入成功！")
                self.logger.info(f"配置已从文件导入: {filepath}")

                # 刷新设置界面
                self.settings_widget.load_settings()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置失败: {str(e)}")
                self.logger.error(f"导入配置失败: {str(e)}")

    def clear_old_logs(self):
        """清理旧日志"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清理30天前的旧日志吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.clear_old_logs(days=30)
                QMessageBox.information(self, "成功", "旧日志清理成功！")
                self.logger.info("旧日志已清理")
                self.logs_widget.load_logs()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理日志失败: {str(e)}")
                self.logger.error(f"清理日志失败: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        version = self.config.get('version', '1.0.0')
        message = f"""
        <h2>TicketMaster</h2>
        <p>版本: {version}</p>
        <p>一个功能完整的 Windows 抢票软件</p>
        <p>支持 12306、大麦网、携程三大平台</p>
        <hr>
        <p>© 2024 TicketMaster. All rights reserved.</p>
        """
        QMessageBox.about(self, "关于 TicketMaster", message)

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        # 询问是否最小化到托盘
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 停止调度器
            self.scheduler.stop()

            # 关闭所有平台连接
            for platform in self.platforms.values():
                platform.close()

            # 记录退出日志
            self.logger.info("应用程序已退出")

            # 隐藏托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()

            event.accept()
        else:
            # 最小化到托盘
            self.hide()
            event.ignore()
