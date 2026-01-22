"""
数据库管理模块
使用 SQLite 数据库存储账号、任务、日志等数据
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from models import Account, AccountStatus, PlatformType
from models import Task, TaskStatus, TaskType


class Database:
    """数据库管理类"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            from utils import get_config
            config = get_config()
            self.db_path = config.get_database_path()

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建账号表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'inactive',
                    nickname TEXT,
                    phone TEXT,
                    email TEXT,
                    cookies TEXT,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    remark TEXT
                )
            ''')

            # 创建任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    task_type TEXT NOT NULL DEFAULT 'once',
                    scheduled_time DATETIME,
                    repeat_interval INTEGER,
                    account_ids TEXT,
                    params TEXT,
                    executed_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_executed DATETIME,
                    next_execute DATETIME,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    remark TEXT
                )
            ''')

            # 创建日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    task_id INTEGER,
                    account_id INTEGER,
                    platform TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    extra_data TEXT
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_time ON tasks(scheduled_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at)')

    # ==================== 账号相关操作 ====================

    def add_account(self, account: Account) -> int:
        """
        添加账号

        Args:
            account: 账号对象

        Returns:
            新账号的 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                INSERT INTO accounts (
                    platform, username, password, status, nickname,
                    phone, email, cookies, last_login, created_at, updated_at, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account.platform.value if isinstance(account.platform, PlatformType) else account.platform,
                account.username,
                account.password,
                account.status.value if isinstance(account.status, AccountStatus) else account.status,
                account.nickname,
                account.phone,
                account.email,
                account.cookies,
                account.last_login,
                now,
                now,
                account.remark
            ))

            return cursor.lastrowid

    def get_account(self, account_id: int) -> Optional[Account]:
        """
        获取账号

        Args:
            account_id: 账号 ID

        Returns:
            账号对象，如果不存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_account(row)
            return None

    def get_all_accounts(self) -> List[Account]:
        """
        获取所有账号

        Returns:
            账号列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts ORDER BY created_at DESC')
            rows = cursor.fetchall()

            return [self._row_to_account(row) for row in rows]

    def get_accounts_by_platform(self, platform: PlatformType) -> List[Account]:
        """
        获取指定平台的所有账号

        Args:
            platform: 平台类型

        Returns:
            账号列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM accounts WHERE platform = ? ORDER BY created_at DESC',
                (platform.value,)
            )
            rows = cursor.fetchall()

            return [self._row_to_account(row) for row in rows]

    def get_accounts_by_status(self, status: AccountStatus) -> List[Account]:
        """
        获取指定状态的所有账号

        Args:
            status: 账号状态

        Returns:
            账号列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM accounts WHERE status = ? ORDER BY created_at DESC',
                (status.value,)
            )
            rows = cursor.fetchall()

            return [self._row_to_account(row) for row in rows]

    def update_account(self, account: Account) -> bool:
        """
        更新账号

        Args:
            account: 账号对象

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                UPDATE accounts SET
                    platform = ?, username = ?, password = ?, status = ?,
                    nickname = ?, phone = ?, email = ?, cookies = ?,
                    last_login = ?, updated_at = ?, remark = ?
                WHERE id = ?
            ''', (
                account.platform.value if isinstance(account.platform, PlatformType) else account.platform,
                account.username,
                account.password,
                account.status.value if isinstance(account.status, AccountStatus) else account.status,
                account.nickname,
                account.phone,
                account.email,
                account.cookies,
                account.last_login,
                now,
                account.remark,
                account.id
            ))

            return cursor.rowcount > 0

    def delete_account(self, account_id: int) -> bool:
        """
        删除账号

        Args:
            account_id: 账号 ID

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            return cursor.rowcount > 0

    def update_account_status(self, account_id: int, status: AccountStatus) -> bool:
        """
        更新账号状态

        Args:
            account_id: 账号 ID
            status: 新状态

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                UPDATE accounts SET status = ?, updated_at = ?
                WHERE id = ?
            ''', (status.value, now, account_id))

            return cursor.rowcount > 0

    def _row_to_account(self, row: sqlite3.Row) -> Account:
        """将数据库行转换为 Account 对象"""
        return Account(
            id=row['id'],
            platform=PlatformType(row['platform']),
            username=row['username'],
            password=row['password'],
            status=AccountStatus(row['status']),
            nickname=row['nickname'] or '',
            phone=row['phone'] or '',
            email=row['email'] or '',
            cookies=row['cookies'] or '',
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            remark=row['remark'] or ''
        )

    # ==================== 任务相关操作 ====================

    def add_task(self, task: Task) -> int:
        """
        添加任务

        Args:
            task: 任务对象

        Returns:
            新任务的 ID
        """
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                INSERT INTO tasks (
                    name, platform, status, task_type, scheduled_time,
                    repeat_interval, account_ids, params,
                    executed_count, success_count, last_executed, next_execute,
                    error_message, created_at, updated_at, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.name,
                task.platform.value if isinstance(task.platform, PlatformType) else task.platform,
                task.status.value if isinstance(task.status, TaskStatus) else task.status,
                task.task_type.value if isinstance(task.task_type, TaskType) else task.task_type,
                task.scheduled_time,
                task.repeat_interval,
                json.dumps(task.account_ids),
                task.params,
                task.executed_count,
                task.success_count,
                task.last_executed,
                task.next_execute,
                task.error_message,
                now,
                now,
                task.remark
            ))

            return cursor.lastrowid

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务 ID

        Returns:
            任务对象，如果不存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_task(row)
            return None

    def get_all_tasks(self) -> List[Task]:
        """
        获取所有任务

        Returns:
            任务列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
            rows = cursor.fetchall()

            return [self._row_to_task(row) for row in rows]

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        获取指定状态的所有任务

        Args:
            status: 任务状态

        Returns:
            任务列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC',
                (status.value,)
            )
            rows = cursor.fetchall()

            return [self._row_to_task(row) for row in rows]

    def get_pending_tasks(self) -> List[Task]:
        """
        获取待执行的任务

        Returns:
            任务列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tasks
                WHERE status IN ('pending', 'running')
                ORDER BY scheduled_time ASC
            ''')
            rows = cursor.fetchall()

            return [self._row_to_task(row) for row in rows]

    def update_task(self, task: Task) -> bool:
        """
        更新任务

        Args:
            task: 任务对象

        Returns:
            是否成功
        """
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                UPDATE tasks SET
                    name = ?, platform = ?, status = ?, task_type = ?,
                    scheduled_time = ?, repeat_interval = ?, account_ids = ?, params = ?,
                    executed_count = ?, success_count = ?, last_executed = ?,
                    next_execute = ?, error_message = ?, updated_at = ?, remark = ?
                WHERE id = ?
            ''', (
                task.name,
                task.platform.value if isinstance(task.platform, PlatformType) else task.platform,
                task.status.value if isinstance(task.status, TaskStatus) else task.status,
                task.task_type.value if isinstance(task.task_type, TaskType) else task.task_type,
                task.scheduled_time,
                task.repeat_interval,
                json.dumps(task.account_ids),
                task.params,
                task.executed_count,
                task.success_count,
                task.last_executed,
                task.next_execute,
                task.error_message,
                now,
                task.remark,
                task.id
            ))

            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """
        删除任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            return cursor.rowcount > 0

    def update_task_status(self, task_id: int, status: TaskStatus, error_message: str = "") -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            error_message: 错误消息

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                UPDATE tasks SET status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            ''', (status.value, error_message, now, task_id))

            return cursor.rowcount > 0

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """将数据库行转换为 Task 对象"""
        import json
        return Task(
            id=row['id'],
            name=row['name'],
            platform=PlatformType(row['platform']),
            status=TaskStatus(row['status']),
            task_type=TaskType(row['task_type']),
            scheduled_time=datetime.fromisoformat(row['scheduled_time']) if row['scheduled_time'] else None,
            repeat_interval=row['repeat_interval'],
            account_ids=json.loads(row['account_ids']) if row['account_ids'] else [],
            params=row['params'] or '{}',
            executed_count=row['executed_count'],
            success_count=row['success_count'],
            last_executed=datetime.fromisoformat(row['last_executed']) if row['last_executed'] else None,
            next_execute=datetime.fromisoformat(row['next_execute']) if row['next_execute'] else None,
            error_message=row['error_message'] or '',
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            remark=row['remark'] or ''
        )

    # ==================== 日志相关操作 ====================

    def add_log(self, level: str, message: str, task_id: int = None,
                account_id: int = None, platform: str = None, extra_data: dict = None):
        """
        添加日志

        Args:
            level: 日志级别（INFO, WARNING, ERROR, SUCCESS）
            message: 日志消息
            task_id: 关联的任务 ID
            account_id: 关联的账号 ID
            platform: 平台类型
            extra_data: 额外数据（字典）
        """
        import json
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO logs (
                    level, message, task_id, account_id, platform, extra_data
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                level,
                message,
                task_id,
                account_id,
                platform,
                json.dumps(extra_data) if extra_data else None
            ))

    def get_logs(self, limit: int = 100, offset: int = 0,
                 level: str = None, task_id: int = None) -> List[Dict[str, Any]]:
        """
        获取日志

        Args:
            limit: 返回数量限制
            offset: 偏移量
            level: 日志级别筛选
            task_id: 任务 ID 筛选

        Returns:
            日志列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM logs WHERE 1=1'
            params = []

            if level:
                query += ' AND level = ?'
                params.append(level)

            if task_id:
                query += ' AND task_id = ?'
                params.append(task_id)

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def get_logs_by_platform(self, platform: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取指定平台的日志

        Args:
            platform: 平台类型
            limit: 返回数量限制

        Returns:
            日志列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM logs
                WHERE platform = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (platform, limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_old_logs(self, days: int = 30):
        """
        清理旧日志

        Args:
            days: 保留天数
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM logs
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))

    def get_log_count(self) -> int:
        """
        获取日志总数

        Returns:
            日志数量
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM logs')
            return cursor.fetchone()['count']
