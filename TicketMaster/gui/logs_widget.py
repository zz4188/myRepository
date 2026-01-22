"""
日志查看界面
实现日志的显示、筛选和导出功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QTextEdit, QHeaderView, QMessageBox,
    QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt
from datetime import datetime

from core import Database, Logger


class LogsWidget(QWidget):
    """日志查看部件"""

    def __init__(self, db: Database, logger: Logger):
        super().__init__()
        self.db = db
        self.logger = logger
        self.current_logs = []

        self.init_ui()
        self.load_logs()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 工具栏
        toolbar_layout = QHBoxLayout()

        # 日志级别筛选
        self.level_filter = QComboBox()
        self.level_filter.addItem("全部级别", None)
        self.level_filter.addItem("DEBUG", "DEBUG")
        self.level_filter.addItem("INFO", "INFO")
        self.level_filter.addItem("WARNING", "WARNING")
        self.level_filter.addItem("ERROR", "ERROR")
        self.level_filter.addItem("SUCCESS", "SUCCESS")
        self.level_filter.addItem("CRITICAL", "CRITICAL")
        self.level_filter.currentIndexChanged.connect(self.load_logs)
        toolbar_layout.addWidget(QLabel("级别:"))
        toolbar_layout.addWidget(self.level_filter)

        toolbar_layout.addSpacing(10)

        # 导出日志按钮
        export_button = QPushButton("📥 导出日志")
        export_button.clicked.connect(self.export_logs)
        toolbar_layout.addWidget(export_button)

        toolbar_layout.addSpacing(10)

        # 清除显示按钮
        clear_button = QPushButton("🗑️ 清除显示")
        clear_button.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(clear_button)

        toolbar_layout.addStretch()

        # 刷新按钮
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.load_logs)
        toolbar_layout.addWidget(refresh_button)

        layout.addLayout(toolbar_layout)

        # 日志表格
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(["时间", "级别", "任务ID", "平台", "消息"])
        self.logs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.logs_table.setColumnWidth(0, 180)  # 时间列固定宽度
        self.logs_table.setColumnWidth(1, 80)   # 级别列固定宽度
        self.logs_table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.logs_table, 1)

        # 日志详情
        self.detail_label = QLabel("日志详情:")
        layout.addWidget(self.detail_label)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        layout.addWidget(self.detail_text)

        # 统计信息
        stats_layout = QHBoxLayout()
        self.total_label = QLabel("总计: 0")
        self.info_label = QLabel("INFO: 0")
        self.warning_label = QLabel("WARNING: 0")
        self.error_label = QLabel("ERROR: 0")
        self.success_label = QLabel("SUCCESS: 0")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.info_label)
        stats_layout.addWidget(self.warning_label)
        stats_layout.addWidget(self.error_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def load_logs(self, limit: int = 500):
        """加载日志"""
        level = self.level_filter.currentData()

        if level:
            self.current_logs = self.db.get_logs(limit=limit, level=level)
        else:
            self.current_logs = self.db.get_logs(limit=limit)

        self.update_table()
        self.update_stats()

    def update_table(self):
        """更新表格显示"""
        self.logs_table.setRowCount(0)

        for row, log in enumerate(self.current_logs):
            self.logs_table.insertRow(row)

            # 时间
            time_text = log['created_at']
            if isinstance(time_text, str):
                time_text = time_text[:19] if len(time_text) >= 19 else time_text
            self.logs_table.setItem(row, 0, QTableWidgetItem(time_text))

            # 级别
            level_item = QTableWidgetItem(log['level'])
            # 设置级别颜色
            color = self._get_level_color(log['level'])
            if color:
                level_item.setForeground(color)
            self.logs_table.setItem(row, 1, level_item)

            # 任务ID
            task_id = str(log['task_id']) if log['task_id'] else ''
            self.logs_table.setItem(row, 2, QTableWidgetItem(task_id))

            # 平台
            platform = log['platform'] or ''
            self.logs_table.setItem(row, 3, QTableWidgetItem(platform))

            # 消息
            message = log['message']
            if message:
                # 截断长消息
                if len(message) > 100:
                    message = message[:100] + '...'
            self.logs_table.setItem(row, 4, QTableWidgetItem(message))

    def _get_level_color(self, level: str):
        """获取级别对应的颜色"""
        color_map = {
            'DEBUG': Qt.GlobalColor.gray,
            'INFO': Qt.GlobalColor.blue,
            'WARNING': Qt.GlobalColor.darkYellow,
            'ERROR': Qt.GlobalColor.red,
            'SUCCESS': Qt.GlobalColor.green,
            'CRITICAL': Qt.GlobalColor.red
        }
        return color_map.get(level)

    def update_stats(self):
        """更新统计信息"""
        total = len(self.current_logs)
        info_count = sum(1 for log in self.current_logs if log['level'] == 'INFO')
        warning_count = sum(1 for log in self.current_logs if log['level'] == 'WARNING')
        error_count = sum(1 for log in self.current_logs if log['level'] == 'ERROR')
        success_count = sum(1 for log in self.current_logs if log['level'] == 'SUCCESS')

        self.total_label.setText(f"总计: {total}")
        self.info_label.setText(f"INFO: {info_count}")
        self.warning_label.setText(f"WARNING: {warning_count}")
        self.error_label.setText(f"ERROR: {error_count}")
        self.success_label.setText(f"SUCCESS: {success_count}")

    def on_selection_changed(self):
        """选择改变事件"""
        selected_items = self.logs_table.selectedItems()
        if not selected_items:
            self.detail_text.clear()
            return

        row = selected_items[0].row()
        log = self.current_logs[row]

        # 显示详情
        detail_text = f"时间: {log['created_at']}\n"
        detail_text += f"级别: {log['level']}\n"
        if log['task_id']:
            detail_text += f"任务ID: {log['task_id']}\n"
        if log['account_id']:
            detail_text += f"账号ID: {log['account_id']}\n"
        if log['platform']:
            detail_text += f"平台: {log['platform']}\n"
        detail_text += f"消息: {log['message']}\n"

        if log['extra_data']:
            import json
            try:
                extra = json.loads(log['extra_data'])
                detail_text += f"额外数据:\n{json.dumps(extra, indent=2, ensure_ascii=False)}"
            except:
                detail_text += f"额外数据: {log['extra_data']}"

        self.detail_text.setText(detail_text)

    def clear_logs(self):
        """清除显示的日志"""
        self.logs_table.setRowCount(0)
        self.detail_text.clear()
        self.current_logs.clear()
        self.update_stats()

    def export_logs(self):
        """导出日志"""
        if not self.current_logs:
            QMessageBox.information(self, "提示", "没有日志可导出！")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv);;Text Files (*.txt)"
        )

        if not filepath:
            return

        try:
            if filepath.endswith('.csv'):
                self._export_csv(filepath)
            else:
                self._export_txt(filepath)

            QMessageBox.information(self, "成功", f"日志已导出到:\n{filepath}")
            self.logger.info(f"日志已导出到: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出日志失败: {str(e)}")
            self.logger.error(f"导出日志失败: {str(e)}")

    def _export_csv(self, filepath: str):
        """导出为 CSV 格式"""
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '级别', '任务ID', '账号ID', '平台', '消息'])

            for log in self.current_logs:
                writer.writerow([
                    log['created_at'],
                    log['level'],
                    log['task_id'] or '',
                    log['account_id'] or '',
                    log['platform'] or '',
                    log['message']
                ])

    def _export_txt(self, filepath: str):
        """导出为 TXT 格式"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for log in self.current_logs:
                line = f"[{log['created_at']}] [{log['level']}]"
                if log['task_id']:
                    line += f" [任务:{log['task_id']}]"
                if log['platform']:
                    line += f" [{log['platform']}]"
                line += f" {log['message']}\n"
                f.write(line)

    def add_log_to_table(self, level: str, message: str, task_id: int = None,
                        account_id: int = None, platform: str = None):
        """
        添加日志到表格（实时添加）

        Args:
            level: 日志级别
            message: 日志消息
            task_id: 任务ID
            account_id: 账号ID
            platform: 平台
        """
        log = {
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'task_id': task_id,
            'account_id': account_id,
            'platform': platform,
            'message': message,
            'extra_data': None
        }

        self.current_logs.insert(0, log)

        # 添加到表格
        self.logs_table.insertRow(0)

        time_text = log['created_at']
        self.logs_table.setItem(0, 0, QTableWidgetItem(time_text))

        level_item = QTableWidgetItem(log['level'])
        color = self._get_level_color(log['level'])
        if color:
            level_item.setForeground(color)
        self.logs_table.setItem(0, 1, level_item)

        task_id_text = str(task_id) if task_id else ''
        self.logs_table.setItem(0, 2, QTableWidgetItem(task_id_text))

        platform_text = platform or ''
        self.logs_table.setItem(0, 3, QTableWidgetItem(platform_text))

        message_text = message
        if len(message_text) > 100:
            message_text = message_text[:100] + '...'
        self.logs_table.setItem(0, 4, QTableWidgetItem(message_text))

        # 更新统计
        self.update_stats()
