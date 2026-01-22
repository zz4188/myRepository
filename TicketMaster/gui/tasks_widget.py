"""
任务管理界面
实现抢票任务的创建、编辑、删除和执行管理功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QLineEdit, QDialog, QFormLayout,
    QMessageBox, QHeaderView, QDialogButtonBox, QGroupBox, QTextEdit,
    QDateEdit, QTimeEdit, QSpinBox, QTabWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate, QTime
from datetime import datetime, timedelta

from core import Database, Logger, TaskScheduler
from models import Task, PlatformType, TaskStatus, TaskType
from platforms import BasePlatform


class TaskDialog(QDialog):
    """任务编辑对话框"""

    def __init__(self, task: Task = None, accounts: list = None, parent=None):
        super().__init__(parent)
        self.task = task or Task()
        self.accounts = accounts or []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("编辑任务" if self.task.id else "创建任务")
        self.setMinimumWidth(600)

        layout = QVBoxLayout()

        # 标签页
        tab_widget = QTabWidget()

        # 基本信息页
        basic_tab = QWidget()
        basic_layout = QFormLayout()

        # 任务名称
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.task.name)
        basic_layout.addRow("任务名称 *:", self.name_edit)

        # 平台选择
        self.platform_combo = QComboBox()
        for platform in PlatformType:
            self.platform_combo.addItem(platform.display_name(), platform)
        if self.task.id:
            self.platform_combo.setCurrentText(self.task.platform.display_name())
        self.platform_combo.currentIndexChanged.connect(self.on_platform_changed)
        basic_layout.addRow("平台 *:", self.platform_combo)

        # 任务类型
        self.task_type_combo = QComboBox()
        for task_type in TaskType:
            self.task_type_combo.addItem(task_type.display_name(), task_type)
        if self.task.id:
            self.task_type_combo.setCurrentText(self.task_type.display_name())
        self.task_type_combo.currentIndexChanged.connect(self.on_task_type_changed)
        basic_layout.addRow("任务类型:", self.task_type_combo)

        # 执行时间
        self.datetime_edit = QDateTimeEditWidget()
        if self.task.scheduled_time:
            self.datetime_edit.setDateTime(self.task.scheduled_time)
        basic_layout.addRow("执行时间:", self.datetime_edit)

        # 重复间隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(86400)  # 最大24小时
        self.interval_spin.setValue(self.task.repeat_interval or 3600)
        self.interval_spin.setSuffix(" 秒")
        basic_layout.addRow("重复间隔:", self.interval_spin)

        # 备注
        self.remark_edit = QTextEdit()
        self.remark_edit.setMaximumHeight(60)
        self.remark_edit.setText(self.task.remark)
        basic_layout.addRow("备注:", self.remark_edit)

        basic_tab.setLayout(basic_layout)
        tab_widget.addTab(basic_tab, "基本信息")

        # 账号选择页
        accounts_tab = QWidget()
        accounts_layout = QVBoxLayout()

        # 账号列表
        self.accounts_list = QListWidget()
        for account in self.accounts:
            item = QListWidgetItem(f"{account.platform.display_name()} - {account.username}")
            item.setData(Qt.ItemDataRole.UserRole, account.id)
            if account.id in self.task.account_ids:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.accounts_list.addItem(item)

        accounts_layout.addWidget(QLabel("选择使用的账号（可多选）:"))
        accounts_layout.addWidget(self.accounts_list)
        accounts_tab.setLayout(accounts_layout)
        tab_widget.addTab(accounts_tab, "账号选择")

        # 任务参数页
        params_tab = QWidget()
        params_layout = QFormLayout()

        # 出发地
        self.from_edit = QLineEdit()
        params_layout.addRow("出发地/城市:", self.from_edit)

        # 目的地
        self.to_edit = QLineEdit()
        params_layout.addRow("目的地/城市:", self.to_edit)

        # 日期
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        params_layout.addRow("日期:", self.date_edit)

        # 座位类型/票档
        self.seat_type_edit = QLineEdit()
        params_layout.addRow("座位类型/票档:", self.seat_type_edit)

        # 数量
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10)
        self.quantity_spin.setValue(1)
        params_layout.addRow("购买数量:", self.quantity_spin)

        # 价格范围
        self.price_range_edit = QLineEdit()
        self.price_range_edit.setPlaceholderText("例如: 0-500")
        params_layout.addRow("价格范围:", self.price_range_edit)

        params_tab.setLayout(params_layout)
        tab_widget.addTab(params_tab, "任务参数")

        layout.addWidget(tab_widget)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # 更新界面状态
        self.on_task_type_changed()

    def on_platform_changed(self):
        """平台改变事件"""
        platform = self.platform_combo.currentData()
        # 根据平台调整显示的参数
        pass

    def on_task_type_changed(self):
        """任务类型改变事件"""
        task_type = self.task_type_combo.currentData()
        # 根据任务类型启用/禁用相关控件
        is_repeat = task_type != TaskType.ONCE
        self.interval_spin.setEnabled(is_repeat)

    def get_task(self) -> Task:
        """获取任务信息"""
        platform = self.platform_combo.currentData()
        task_type = self.task_type_combo.currentData()
        scheduled_time = self.datetime_edit.dateTime()

        # 获取选中的账号
        account_ids = []
        for i in range(self.accounts_list.count()):
            item = self.accounts_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                account_ids.append(item.data(Qt.ItemDataRole.UserRole))

        # 构建任务参数
        params = {
            'search': {
                'from': self.from_edit.text(),
                'to': self.to_edit.text(),
                'date': self.date_edit.date().toString('yyyy-MM-dd'),
                'type': 'hotel'  # 默认类型，实际应根据平台调整
            },
            'order': {
                'seat_type': self.seat_type_edit.text(),
                'quantity': self.quantity_spin.value(),
                'price_range': self.price_range_edit.text()
            }
        }

        task = Task(
            id=self.task.id,
            name=self.name_edit.text(),
            platform=platform,
            task_type=task_type,
            scheduled_time=scheduled_time.toPyDateTime() if scheduled_time else None,
            repeat_interval=self.interval_spin.value() if task_type != TaskType.ONCE else None,
            account_ids=account_ids,
            remark=self.remark_edit.toPlainText()
        )
        task.set_params(params)

        return task


class QDateTimeEditWidget(QWidget):
    """日期时间编辑器组合控件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())

        layout.addWidget(self.date_edit)
        layout.addWidget(self.time_edit)
        self.setLayout(layout)

    def dateTime(self):
        """获取日期时间"""
        date = self.date_edit.date()
        time = self.time_edit.time()
        return datetime(date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())

    def setDateTime(self, dt: datetime):
        """设置日期时间"""
        self.date_edit.setDate(QDate(dt.year, dt.month, dt.day))
        self.time_edit.setTime(QTime(dt.hour, dt.minute, dt.second))


class TasksWidget(QWidget):
    """任务管理部件"""

    def __init__(self, db: Database, logger: Logger, platforms: dict, scheduler: TaskScheduler):
        super().__init__()
        self.db = db
        self.logger = logger
        self.platforms = platforms
        self.scheduler = scheduler
        self.current_tasks = []

        self.init_ui()
        self.load_tasks()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 状态筛选
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", None)
        for status in TaskStatus:
            self.status_filter.addItem(status.display_name(), status)
        self.status_filter.currentIndexChanged.connect(self.load_tasks)
        toolbar_layout.addWidget(QLabel("状态:"))
        toolbar_layout.addWidget(self.status_filter)

        toolbar_layout.addSpacing(10)

        # 添加任务按钮
        add_button = QPushButton("➕ 创建任务")
        add_button.clicked.connect(self.add_task)
        toolbar_layout.addWidget(add_button)

        # 编辑任务按钮
        self.edit_button = QPushButton("✏️ 编辑")
        self.edit_button.clicked.connect(self.edit_task)
        self.edit_button.setEnabled(False)
        toolbar_layout.addWidget(self.edit_button)

        # 删除任务按钮
        self.delete_button = QPushButton("🗑️ 删除")
        self.delete_button.clicked.connect(self.delete_task)
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)

        # 暂停/恢复任务按钮
        self.pause_button = QPushButton("⏸️ 暂停")
        self.pause_button.clicked.connect(self.pause_or_resume_task)
        self.pause_button.setEnabled(False)
        toolbar_layout.addWidget(self.pause_button)

        # 立即执行按钮
        self.run_button = QPushButton("▶️ 立即执行")
        self.run_button.clicked.connect(self.run_task_now)
        self.run_button.setEnabled(False)
        toolbar_layout.addWidget(self.run_button)

        toolbar_layout.addStretch()

        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.load_tasks)
        toolbar_layout.addWidget(refresh_button)

        layout.addLayout(toolbar_layout)

        # 任务列表
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(9)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "名称", "平台", "状态", "类型", "执行时间", "执行次数", "成功次数", "备注"
        ])
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tasks_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tasks_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.tasks_table.itemDoubleClicked.connect(self.edit_task)
        layout.addWidget(self.tasks_table)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("总计: 0")
        self.running_label = QLabel("运行中: 0")
        self.pending_label = QLabel("等待中: 0")
        self.success_label = QLabel("成功: 0")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.running_label)
        stats_layout.addWidget(self.pending_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def load_tasks(self):
        """加载任务列表"""
        status = self.status_filter.currentData()

        if status:
            self.current_tasks = self.db.get_tasks_by_status(status)
        else:
            self.current_tasks = self.db.get_all_tasks()

        self.update_table()
        self.update_stats()

    def update_table(self):
        """更新表格显示"""
        self.tasks_table.setRowCount(0)

        for row, task in enumerate(self.current_tasks):
            self.tasks_table.insertRow(row)

            # ID
            item = QTableWidgetItem(str(task.id))
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.tasks_table.setItem(row, 0, item)

            # 名称
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task.name))

            # 平台
            self.tasks_table.setItem(row, 2, QTableWidgetItem(task.platform.display_name()))

            # 状态
            status_item = QTableWidgetItem(task.status.display_name())
            # 设置状态颜色
            if task.status == TaskStatus.RUNNING:
                status_item.setForeground(Qt.GlobalColor.blue)
            elif task.status == TaskStatus.SUCCESS:
                status_item.setForeground(Qt.GlobalColor.green)
            elif task.status == TaskStatus.FAILED:
                status_item.setForeground(Qt.GlobalColor.red)
            elif task.status == TaskStatus.PAUSED:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.tasks_table.setItem(row, 3, status_item)

            # 类型
            self.tasks_table.setItem(row, 4, QTableWidgetItem(task.task_type.display_name()))

            # 执行时间
            next_time = task.next_execute or task.scheduled_time
            time_text = next_time.strftime('%Y-%m-%d %H:%M:%S') if next_time else '未设置'
            self.tasks_table.setItem(row, 5, QTableWidgetItem(time_text))

            # 执行次数
            self.tasks_table.setItem(row, 6, QTableWidgetItem(str(task.executed_count)))

            # 成功次数
            self.tasks_table.setItem(row, 7, QTableWidgetItem(str(task.success_count)))

            # 备注
            self.tasks_table.setItem(row, 8, QTableWidgetItem(task.remark))

    def update_stats(self):
        """更新统计信息"""
        total = len(self.current_tasks)
        running = sum(1 for task in self.current_tasks if task.status == TaskStatus.RUNNING)
        pending = sum(1 for task in self.current_tasks if task.status == TaskStatus.PENDING)
        success = sum(1 for task in self.current_tasks if task.status == TaskStatus.SUCCESS)

        self.total_label.setText(f"总计: {total}")
        self.running_label.setText(f"运行中: {running}")
        self.pending_label.setText(f"等待中: {pending}")
        self.success_label.setText(f"成功: {success}")

    def on_selection_changed(self):
        """选择改变事件"""
        has_selection = len(self.tasks_table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.pause_button.setEnabled(has_selection)
        self.run_button.setEnabled(has_selection)

        # 更新暂停按钮文本
        if has_selection:
            task = self.get_selected_task()
            if task and task.status == TaskStatus.PAUSED:
                self.pause_button.setText("▶️ 恢复")
            else:
                self.pause_button.setText("⏸️ 暂停")

    def get_selected_task(self) -> Task:
        """获取选中的任务"""
        selected_items = self.tasks_table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        task_id = self.tasks_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return self.db.get_task(task_id)

    def add_task(self):
        """添加任务"""
        accounts = self.db.get_all_accounts()
        if not accounts:
            QMessageBox.warning(self, "警告", "请先添加账号！")
            return

        dialog = TaskDialog(accounts=accounts, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task = dialog.get_task()
            if not task.name:
                QMessageBox.warning(self, "警告", "请输入任务名称！")
                return

            if not task.account_ids:
                QMessageBox.warning(self, "警告", "请至少选择一个账号！")
                return

            try:
                task_id = self.db.add_task(task)
                self.logger.info(f"添加任务成功: {task.name}")

                # 添加到调度器
                loaded_task = self.db.get_task(task_id)
                if loaded_task:
                    self.scheduler.add_task(loaded_task, self.parent().execute_task)

                QMessageBox.information(self, "成功", "任务创建成功！")
                self.load_tasks()
            except Exception as e:
                self.logger.error(f"添加任务失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加任务失败: {str(e)}")

    def edit_task(self):
        """编辑任务"""
        task = self.get_selected_task()
        if not task:
            return

        accounts = self.db.get_all_accounts()
        dialog = TaskDialog(task, accounts, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_task = dialog.get_task()
            try:
                success = self.db.update_task(updated_task)
                if success:
                    self.logger.info(f"更新任务成功: {updated_task.name}")

                    # 重新调度任务
                    loaded_task = self.db.get_task(updated_task.id)
                    if loaded_task:
                        self.scheduler.reschedule_task(loaded_task, self.parent().execute_task)

                    QMessageBox.information(self, "成功", "任务更新成功！")
                    self.load_tasks()
                else:
                    QMessageBox.warning(self, "警告", "任务更新失败！")
            except Exception as e:
                self.logger.error(f"更新任务失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"更新任务失败: {str(e)}")

    def delete_task(self):
        """删除任务"""
        task = self.get_selected_task()
        if not task:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除任务 '{task.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 从调度器中移除
                self.scheduler.remove_task(task.id)

                # 从数据库中删除
                success = self.db.delete_task(task.id)
                if success:
                    self.logger.info(f"删除任务成功: {task.name}")
                    QMessageBox.information(self, "成功", "任务删除成功！")
                    self.load_tasks()
                else:
                    QMessageBox.warning(self, "警告", "任务删除失败！")
            except Exception as e:
                self.logger.error(f"删除任务失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除任务失败: {str(e)}")

    def pause_or_resume_task(self):
        """暂停或恢复任务"""
        task = self.get_selected_task()
        if not task:
            return

        try:
            if task.status == TaskStatus.PAUSED:
                # 恢复任务
                self.scheduler.resume_task(task.id)
                QMessageBox.information(self, "成功", "任务已恢复！")
            else:
                # 暂停任务
                self.scheduler.pause_task(task.id)
                QMessageBox.information(self, "成功", "任务已暂停！")

            self.load_tasks()
        except Exception as e:
            self.logger.error(f"暂停/恢复任务失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def run_task_now(self):
        """立即执行任务"""
        task = self.get_selected_task()
        if not task:
            return

        reply = QMessageBox.question(
            self,
            "确认执行",
            f"确定要立即执行任务 '{task.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 在后台线程中执行任务
                from PyQt6.QtCore import QThread
                import threading

                def execute():
                    result = self.parent().execute_task(task)
                    # 执行完成后刷新列表
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(100, self.load_tasks)

                thread = threading.Thread(target=execute, daemon=True)
                thread.start()

                QMessageBox.information(self, "提示", "任务已开始执行，请查看日志了解详情。")
            except Exception as e:
                self.logger.error(f"执行任务失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"执行任务失败: {str(e)}")
