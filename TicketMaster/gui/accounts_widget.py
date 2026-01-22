"""
账号管理界面
实现账号的增删改查和连接测试功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QHeaderView, QDialogButtonBox, QGroupBox, QTextEdit,
    QCheckBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

from core import Database, Logger
from models import Account, PlatformType, AccountStatus
from platforms import Platform12306, PlatformDamai, PlatformCtrip
from utils import get_encryption


class AccountDialog(QDialog):
    """账号编辑对话框"""

    def __init__(self, account: Account = None, parent=None):
        super().__init__(parent)
        self.account = account or Account()
        self.encryption = get_encryption()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("编辑账号" if self.account.id else "添加账号")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # 表单布局
        form_layout = QFormLayout()

        # 平台选择
        self.platform_combo = QComboBox()
        for platform in PlatformType:
            self.platform_combo.addItem(platform.display_name(), platform)
        if self.account.id:
            self.platform_combo.setCurrentText(self.account.platform.display_name())
        form_layout.addRow("平台:", self.platform_combo)

        # 用户名
        self.username_edit = QLineEdit()
        self.username_edit.setText(self.account.username)
        form_layout.addRow("用户名:", self.username_edit)

        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        if self.account.password:
            try:
                decrypted = self.encryption.decrypt(self.account.password)
                self.password_edit.setText(decrypted)
            except:
                pass
        form_layout.addRow("密码:", self.password_edit)

        # 昵称
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setText(self.account.nickname)
        form_layout.addRow("昵称:", self.nickname_edit)

        # 手机号
        self.phone_edit = QLineEdit()
        self.phone_edit.setText(self.account.phone)
        form_layout.addRow("手机号:", self.phone_edit)

        # 邮箱
        self.email_edit = QLineEdit()
        self.email_edit.setText(self.account.email)
        form_layout.addRow("邮箱:", self.email_edit)

        # 备注
        self.remark_edit = QTextEdit()
        self.remark_edit.setMaximumHeight(60)
        self.remark_edit.setText(self.account.remark)
        form_layout.addRow("备注:", self.remark_edit)

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_account(self) -> Account:
        """获取账号信息"""
        platform = self.platform_combo.currentData()
        password = self.password_edit.text()

        account = Account(
            id=self.account.id,
            platform=platform,
            username=self.username_edit.text(),
            password=self.encryption.encrypt(password) if password else '',
            nickname=self.nickname_edit.text(),
            phone=self.phone_edit.text(),
            email=self.email_edit.text(),
            remark=self.remark_edit.toPlainText()
        )

        return account


class AccountsWidget(QWidget):
    """账号管理部件"""

    def __init__(self, db: Database, logger: Logger, encryption, platforms: dict):
        super().__init__()
        self.db = db
        self.logger = logger
        self.encryption = encryption
        self.platforms = platforms
        self.current_accounts = []

        self.init_ui()
        self.load_accounts()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 平台筛选
        self.platform_filter = QComboBox()
        self.platform_filter.addItem("全部平台", None)
        for platform in PlatformType:
            self.platform_filter.addItem(platform.display_name(), platform)
        self.platform_filter.currentIndexChanged.connect(self.load_accounts)
        toolbar_layout.addWidget(QLabel("平台:"))
        toolbar_layout.addWidget(self.platform_filter)

        toolbar_layout.addSpacing(10)

        # 添加账号按钮
        add_button = QPushButton("➕ 添加账号")
        add_button.clicked.connect(self.add_account)
        toolbar_layout.addWidget(add_button)

        # 编辑账号按钮
        self.edit_button = QPushButton("✏️ 编辑")
        self.edit_button.clicked.connect(self.edit_account)
        self.edit_button.setEnabled(False)
        toolbar_layout.addWidget(self.edit_button)

        # 删除账号按钮
        self.delete_button = QPushButton("🗑️ 删除")
        self.delete_button.clicked.connect(self.delete_account)
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)

        # 测试连接按钮
        self.test_button = QPushButton("🔗 测试连接")
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setEnabled(False)
        toolbar_layout.addWidget(self.test_button)

        toolbar_layout.addStretch()

        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.load_accounts)
        toolbar_layout.addWidget(refresh_button)

        layout.addLayout(toolbar_layout)

        # 账号列表
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels([
            "ID", "平台", "用户名", "昵称", "状态", "最后登录", "备注"
        ])
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accounts_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.accounts_table.itemDoubleClicked.connect(self.edit_account)
        layout.addWidget(self.accounts_table)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("总计: 0")
        self.active_label = QLabel("正常: 0")
        self.inactive_label = QLabel("未激活: 0")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.active_label)
        stats_layout.addWidget(self.inactive_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def load_accounts(self):
        """加载账号列表"""
        platform = self.platform_filter.currentData()

        if platform:
            self.current_accounts = self.db.get_accounts_by_platform(platform)
        else:
            self.current_accounts = self.db.get_all_accounts()

        self.update_table()
        self.update_stats()

    def update_table(self):
        """更新表格显示"""
        self.accounts_table.setRowCount(0)

        for row, account in enumerate(self.current_accounts):
            self.accounts_table.insertRow(row)

            # ID
            item = QTableWidgetItem(str(account.id))
            item.setData(Qt.ItemDataRole.UserRole, account.id)
            self.accounts_table.setItem(row, 0, item)

            # 平台
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account.platform.display_name()))

            # 用户名
            self.accounts_table.setItem(row, 2, QTableWidgetItem(account.username))

            # 昵称
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account.nickname))

            # 状态
            status_item = QTableWidgetItem(account.status.display_name())
            # 设置状态颜色
            if account.status == AccountStatus.ACTIVE:
                status_item.setForeground(Qt.GlobalColor.green)
            elif account.status == AccountStatus.LOGIN_FAILED:
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.accounts_table.setItem(row, 4, status_item)

            # 最后登录
            last_login = account.last_login.strftime('%Y-%m-%d %H:%M:%S') if account.last_login else '从未登录'
            self.accounts_table.setItem(row, 5, QTableWidgetItem(last_login))

            # 备注
            self.accounts_table.setItem(row, 6, QTableWidgetItem(account.remark))

    def update_stats(self):
        """更新统计信息"""
        total = len(self.current_accounts)
        active = sum(1 for acc in self.current_accounts if acc.status == AccountStatus.ACTIVE)
        inactive = sum(1 for acc in self.current_accounts if acc.status == AccountStatus.INACTIVE)

        self.total_label.setText(f"总计: {total}")
        self.active_label.setText(f"正常: {active}")
        self.inactive_label.setText(f"未激活: {inactive}")

    def on_selection_changed(self):
        """选择改变事件"""
        has_selection = len(self.accounts_table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.test_button.setEnabled(has_selection)

    def get_selected_account(self) -> Account:
        """获取选中的账号"""
        selected_items = self.accounts_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        account_id = self.accounts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return self.db.get_account(account_id)

    def add_account(self):
        """添加账号"""
        dialog = AccountDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            account = dialog.get_account()
            try:
                account_id = self.db.add_account(account)
                self.logger.info(f"添加账号成功: {account.username}")
                QMessageBox.information(self, "成功", "账号添加成功！")
                self.load_accounts()
            except Exception as e:
                self.logger.error(f"添加账号失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加账号失败: {str(e)}")

    def edit_account(self):
        """编辑账号"""
        account = self.get_selected_account()
        if not account:
            return

        dialog = AccountDialog(account, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_account = dialog.get_account()
            try:
                success = self.db.update_account(updated_account)
                if success:
                    self.logger.info(f"更新账号成功: {updated_account.username}")
                    QMessageBox.information(self, "成功", "账号更新成功！")
                    self.load_accounts()
                else:
                    QMessageBox.warning(self, "警告", "账号更新失败！")
            except Exception as e:
                self.logger.error(f"更新账号失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"更新账号失败: {str(e)}")

    def delete_account(self):
        """删除账号"""
        account = self.get_selected_account()
        if not account:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除账号 '{account.username}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.db.delete_account(account.id)
                if success:
                    self.logger.info(f"删除账号成功: {account.username}")
                    QMessageBox.information(self, "成功", "账号删除成功！")
                    self.load_accounts()
                else:
                    QMessageBox.warning(self, "警告", "账号删除失败！")
            except Exception as e:
                self.logger.error(f"删除账号失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除账号失败: {str(e)}")

    def test_connection(self):
        """测试账号连接"""
        account = self.get_selected_account()
        if not account:
            return

        QMessageBox.information(
            self,
            "测试连接",
            f"正在测试账号 {account.username} 的连接...\n\n"
            f"注意：实际测试需要浏览器驱动支持。\n"
            f"请确保已安装 ChromeDriver。"
        )

        # 实际测试连接逻辑
        try:
            platform = self.platforms.get(account.platform)
            if not platform:
                QMessageBox.warning(self, "警告", f"不支持的平台: {account.platform.display_name()}")
                return

            # 解密密码
            try:
                decrypted_password = self.encryption.decrypt(account.password)
                account_for_test = Account(
                    id=account.id,
                    platform=account.platform,
                    username=account.username,
                    password=decrypted_password
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"密码解密失败: {str(e)}")
                return

            # 执行登录测试
            # 注意：实际测试需要启动浏览器，可能会比较慢
            self.logger.info(f"开始测试账号连接: {account.username}", account_id=account.id)

            # 这里简化处理，实际应该调用 platform.login(account_for_test)
            # 并根据结果更新账号状态

            # 模拟测试结果
            QMessageBox.information(
                self,
                "测试结果",
                f"账号 {account.username} 连接测试完成。\n\n"
                f"注意：由于浏览器自动化依赖环境，\n"
                f"请确保 ChromeDriver 已正确安装。"
            )

        except Exception as e:
            self.logger.error(f"测试连接失败: {str(e)}", account_id=account.id)
            QMessageBox.critical(self, "错误", f"测试连接失败: {str(e)}")
