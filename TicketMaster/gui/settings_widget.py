"""
设置界面
实现系统配置的查看和修改功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QCheckBox, QComboBox, QPushButton,
    QLabel, QMessageBox, QFileDialog, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt

from core import Logger
from utils import get_config


class SettingsWidget(QWidget):
    """设置部件"""

    def __init__(self, config, logger: Logger):
        super().__init__()
        self.config = config
        self.logger = logger

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 创建滚动区域
        scroll_layout = QVBoxLayout()

        # ==================== 代理设置 ====================
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QFormLayout()

        self.proxy_enabled = QCheckBox()
        proxy_layout.addRow("启用代理:", self.proxy_enabled)

        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["HTTP", "HTTPS", "SOCKS5"])
        proxy_layout.addRow("代理类型:", self.proxy_type)

        self.proxy_host = QLineEdit()
        proxy_layout.addRow("代理地址:", self.proxy_host)

        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(8080)
        proxy_layout.addRow("代理端口:", self.proxy_port)

        self.proxy_username = QLineEdit()
        proxy_layout.addRow("用户名:", self.proxy_username)

        self.proxy_password = QLineEdit()
        self.proxy_password.setEchoMode(QLineEdit.EchoMode.Password)
        proxy_layout.addRow("密码:", self.proxy_password)

        self.test_proxy_button = QPushButton("测试代理")
        self.test_proxy_button.clicked.connect(self.test_proxy)
        proxy_layout.addRow("", self.test_proxy_button)

        proxy_group.setLayout(proxy_layout)
        scroll_layout.addWidget(proxy_group)

        # ==================== 请求设置 ====================
        request_group = QGroupBox("请求设置")
        request_layout = QFormLayout()

        self.request_timeout = QSpinBox()
        self.request_timeout.setRange(5, 300)
        self.request_timeout.setSuffix(" 秒")
        request_layout.addRow("请求超时:", self.request_timeout)

        self.retry_times = QSpinBox()
        self.retry_times.setRange(0, 10)
        request_layout.addRow("重试次数:", self.retry_times)

        self.retry_delay = QSpinBox()
        self.retry_delay.setRange(1, 60)
        self.retry_delay.setSuffix(" 秒")
        request_layout.addRow("重试延迟:", self.retry_delay)

        self.min_delay = QSpinBox()
        self.min_delay.setRange(0, 10)
        self.min_delay.setSuffix(" 秒")
        request_layout.addRow("最小延迟:", self.min_delay)

        self.max_delay = QSpinBox()
        self.max_delay.setRange(1, 60)
        self.max_delay.setSuffix(" 秒")
        request_layout.addRow("最大延迟:", self.max_delay)

        request_group.setLayout(request_layout)
        scroll_layout.addWidget(request_group)

        # ==================== 抢票设置 ====================
        ticket_group = QGroupBox("抢票设置")
        ticket_layout = QFormLayout()

        self.auto_retry = QCheckBox()
        ticket_layout.addRow("自动重试:", self.auto_retry)

        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 60)
        self.check_interval.setSuffix(" 秒")
        ticket_layout.addRow("检查间隔:", self.check_interval)

        self.max_duration = QSpinBox()
        self.max_duration.setRange(60, 3600)
        self.max_duration.setSuffix(" 秒")
        ticket_layout.addRow("最大抢票时长:", self.max_duration)

        self.order_timeout = QSpinBox()
        self.order_timeout.setRange(10, 300)
        self.order_timeout.setSuffix(" 秒")
        ticket_layout.addRow("下单超时:", self.order_timeout)

        ticket_group.setLayout(ticket_layout)
        scroll_layout.addWidget(ticket_group)

        # ==================== 浏览器设置 ====================
        browser_group = QGroupBox("浏览器设置")
        browser_layout = QFormLayout()

        self.browser_type = QComboBox()
        self.browser_type.addItems(["Chrome", "Firefox", "Edge"])
        browser_layout.addRow("浏览器类型:", self.browser_type)

        self.headless_mode = QCheckBox()
        browser_layout.addRow("无头模式:", self.headless_mode)

        self.driver_path = QLineEdit()
        self.driver_path.setPlaceholderText("留空则自动查找")
        browser_layout.addRow("驱动路径:", self.driver_path)

        self.browse_driver_button = QPushButton("浏览...")
        self.browse_driver_button.clicked.connect(self.browse_driver)
        browser_layout.addRow("", self.browse_driver_button)

        browser_group.setLayout(browser_layout)
        scroll_layout.addWidget(browser_group)

        # ==================== 日志设置 ====================
        logging_group = QGroupBox("日志设置")
        logging_layout = QFormLayout()

        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        logging_layout.addRow("日志级别:", self.log_level)

        self.console_output = QCheckBox()
        logging_layout.addRow("控制台输出:", self.console_output)

        self.file_output = QCheckBox()
        logging_layout.addRow("文件输出:", self.file_output)

        self.log_retention_days = QSpinBox()
        self.log_retention_days.setRange(1, 365)
        self.log_retention_days.setSuffix(" 天")
        logging_layout.addRow("日志保留:", self.log_retention_days)

        logging_group.setLayout(logging_layout)
        scroll_layout.addWidget(logging_group)

        # ==================== 通知设置 ====================
        notification_group = QGroupBox("通知设置")
        notification_layout = QFormLayout()

        self.notification_enabled = QCheckBox()
        notification_layout.addRow("启用通知:", self.notification_enabled)

        self.notification_sound = QCheckBox()
        notification_layout.addRow("声音提示:", self.notification_sound)

        self.notification_popup = QCheckBox()
        notification_layout.addRow("弹窗提示:", self.notification_popup)

        notification_group.setLayout(notification_layout)
        scroll_layout.addWidget(notification_group)

        scroll_layout.addStretch()

        layout.addLayout(scroll_layout)

        # 底部按钮
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("💾 保存设置")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        self.reset_button = QPushButton("↺ 恢复默认")
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_settings(self):
        """加载设置"""
        # 代理设置
        self.proxy_enabled.setChecked(self.config.get('proxy.enabled', False))
        proxy_type = self.config.get('proxy.type', 'http').upper()
        self.proxy_type.setCurrentText(proxy_type)
        self.proxy_host.setText(self.config.get('proxy.host', ''))
        self.proxy_port.setValue(self.config.get('proxy.port', 8080))
        self.proxy_username.setText(self.config.get('proxy.username', ''))
        self.proxy_password.setText(self.config.get('proxy.password', ''))

        # 请求设置
        self.request_timeout.setValue(self.config.get('request.timeout', 30))
        self.retry_times.setValue(self.config.get('request.retry_times', 3))
        self.retry_delay.setValue(self.config.get('request.retry_delay', 1))
        self.min_delay.setValue(self.config.get('request.min_delay', 0.5))
        self.max_delay.setValue(self.config.get('request.max_delay', 2))

        # 抢票设置
        self.auto_retry.setChecked(self.config.get('ticket.auto_retry', True))
        self.check_interval.setValue(int(self.config.get('ticket.check_interval', 1.0)))
        self.max_duration.setValue(self.config.get('ticket.max_duration', 300))
        self.order_timeout.setValue(self.config.get('ticket.order_timeout', 60))

        # 浏览器设置
        browser_type = self.config.get('browser.type', 'chrome').capitalize()
        self.browser_type.setCurrentText(browser_type)
        self.headless_mode.setChecked(self.config.get('browser.headless', True))
        self.driver_path.setText(self.config.get('browser.driver_path', ''))

        # 日志设置
        self.log_level.setCurrentText(self.config.get('logging.level', 'INFO').upper())
        self.console_output.setChecked(self.config.get('logging.console_output', True))
        self.file_output.setChecked(self.config.get('logging.file_output', True))
        self.log_retention_days.setValue(self.config.get('logging.retention_days', 30))

        # 通知设置
        self.notification_enabled.setChecked(self.config.get('notification.enabled', True))
        self.notification_sound.setChecked(self.config.get('notification.sound', True))
        self.notification_popup.setChecked(self.config.get('notification.popup', True))

    def save_settings(self):
        """保存设置"""
        try:
            # 代理设置
            self.config.set('proxy.enabled', self.proxy_enabled.isChecked(), save=False)
            self.config.set('proxy.type', self.proxy_type.currentText().lower(), save=False)
            self.config.set('proxy.host', self.proxy_host.text(), save=False)
            self.config.set('proxy.port', self.proxy_port.value(), save=False)
            self.config.set('proxy.username', self.proxy_username.text(), save=False)
            self.config.set('proxy.password', self.proxy_password.text(), save=False)

            # 请求设置
            self.config.set('request.timeout', self.request_timeout.value(), save=False)
            self.config.set('request.retry_times', self.retry_times.value(), save=False)
            self.config.set('request.retry_delay', self.retry_delay.value(), save=False)
            self.config.set('request.min_delay', self.min_delay.value(), save=False)
            self.config.set('request.max_delay', self.max_delay.value(), save=False)

            # 抢票设置
            self.config.set('ticket.auto_retry', self.auto_retry.isChecked(), save=False)
            self.config.set('ticket.check_interval', float(self.check_interval.value()), save=False)
            self.config.set('ticket.max_duration', self.max_duration.value(), save=False)
            self.config.set('ticket.order_timeout', self.order_timeout.value(), save=False)

            # 浏览器设置
            self.config.set('browser.type', self.browser_type.currentText().lower(), save=False)
            self.config.set('browser.headless', self.headless_mode.isChecked(), save=False)
            self.config.set('browser.driver_path', self.driver_path.text(), save=False)

            # 日志设置
            self.config.set('logging.level', self.log_level.currentText(), save=False)
            self.config.set('logging.console_output', self.console_output.isChecked(), save=False)
            self.config.set('logging.file_output', self.file_output.isChecked(), save=False)
            self.config.set('logging.retention_days', self.log_retention_days.value(), save=False)

            # 通知设置
            self.config.set('notification.enabled', self.notification_enabled.isChecked(), save=False)
            self.config.set('notification.sound', self.notification_sound.isChecked(), save=False)
            self.config.set('notification.popup', self.notification_popup.isChecked(), save=True)

            QMessageBox.information(self, "成功", "设置保存成功！\n\n部分设置需要重启应用才能生效。")
            self.logger.info("系统设置已更新")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
            self.logger.error(f"保存设置失败: {str(e)}")

    def reset_settings(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config.reset(save=True)
                self.load_settings()
                QMessageBox.information(self, "成功", "设置已恢复默认值！")
                self.logger.info("系统设置已恢复默认")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"恢复默认设置失败: {str(e)}")
                self.logger.error(f"恢复默认设置失败: {str(e)}")

    def browse_driver(self):
        """浏览驱动文件"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "选择浏览器驱动",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )

        if filepath:
            self.driver_path.setText(filepath)

    def test_proxy(self):
        """测试代理连接"""
        if not self.proxy_enabled.isChecked():
            QMessageBox.warning(self, "警告", "请先启用代理！")
            return

        host = self.proxy_host.text()
        port = self.proxy_port.value()

        if not host:
            QMessageBox.warning(self, "警告", "请输入代理地址！")
            return

        from utils import get_proxy_manager
        proxy_manager = get_proxy_manager()

        try:
            from utils.proxy import Proxy
            proxy = Proxy(
                type=self.proxy_type.currentText().lower(),
                host=host,
                port=port,
                username=self.proxy_username.text() or None,
                password=self.proxy_password.text() or None
            )

            if proxy_manager.validate_proxy(proxy):
                QMessageBox.information(self, "成功", "代理连接测试成功！")
                self.logger.info(f"代理测试成功: {host}:{port}")
            else:
                QMessageBox.warning(self, "警告", "代理连接测试失败！")
                self.logger.warning(f"代理测试失败: {host}:{port}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试代理时发生错误: {str(e)}")
            self.logger.error(f"测试代理失败: {str(e)}")
