"""
任务数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from .account import PlatformType


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 等待执行
    RUNNING = "running"           # 执行中
    PAUSED = "paused"             # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 执行失败
    CANCELLED = "cancelled"       # 已取消
    SUCCESS = "success"           # 抢票成功

    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            TaskStatus.PENDING: "等待执行",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.PAUSED: "已暂停",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败",
            TaskStatus.CANCELLED: "已取消",
            TaskStatus.SUCCESS: "成功"
        }
        return names.get(self, self.value)


class TaskType(Enum):
    """任务类型枚举"""
    ONCE = "once"                 # 一次性任务
    REPEAT_DAILY = "daily"        # 每天执行
    REPEAT_WEEKLY = "weekly"      # 每周执行
    REPEAT_MONTHLY = "monthly"    # 每月执行
    REPEAT_CUSTOM = "custom"      # 自定义间隔

    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            TaskType.ONCE: "一次性",
            TaskType.REPEAT_DAILY: "每天",
            TaskType.REPEAT_WEEKLY: "每周",
            TaskType.REPEAT_MONTHLY: "每月",
            TaskType.REPEAT_CUSTOM: "自定义"
        }
        return names.get(self, self.value)


@dataclass
class Task:
    """任务数据模型"""
    id: Optional[int] = None
    name: str = ""
    platform: PlatformType = PlatformType.TICKET_12306
    status: TaskStatus = TaskStatus.PENDING
    task_type: TaskType = TaskType.ONCE

    # 执行时间
    scheduled_time: Optional[datetime] = None  # 计划执行时间
    repeat_interval: Optional[int] = None     # 重复间隔（秒）

    # 关联的账号ID列表
    account_ids: List[int] = field(default_factory=list)

    # 任务参数（JSON 字符串）
    params: str = "{}"

    # 执行信息
    executed_count: int = 0           # 已执行次数
    success_count: int = 0            # 成功次数
    last_executed: Optional[datetime] = None
    next_execute: Optional[datetime] = None
    error_message: str = ""

    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 备注
    remark: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform.value if isinstance(self.platform, PlatformType) else self.platform,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'task_type': self.task_type.value if isinstance(self.task_type, TaskType) else self.task_type,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'repeat_interval': self.repeat_interval,
            'account_ids': self.account_ids,
            'params': self.params,
            'executed_count': self.executed_count,
            'success_count': self.success_count,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'next_execute': self.next_execute.isoformat() if self.next_execute else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'remark': self.remark
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        platform = data.get('platform', PlatformType.TICKET_12306.value)
        if isinstance(platform, str):
            platform = PlatformType.from_string(platform)

        status = data.get('status', TaskStatus.PENDING.value)
        if isinstance(status, str):
            try:
                status = TaskStatus(status)
            except ValueError:
                status = TaskStatus.PENDING

        task_type = data.get('task_type', TaskType.ONCE.value)
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.ONCE

        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            platform=platform,
            status=status,
            task_type=task_type,
            scheduled_time=datetime.fromisoformat(data['scheduled_time']) if data.get('scheduled_time') else None,
            repeat_interval=data.get('repeat_interval'),
            account_ids=data.get('account_ids', []),
            params=data.get('params', '{}'),
            executed_count=data.get('executed_count', 0),
            success_count=data.get('success_count', 0),
            last_executed=datetime.fromisoformat(data['last_executed']) if data.get('last_executed') else None,
            next_execute=datetime.fromisoformat(data['next_execute']) if data.get('next_execute') else None,
            error_message=data.get('error_message', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            remark=data.get('remark', '')
        )

    def get_params(self) -> Dict[str, Any]:
        """获取参数字典"""
        import json
        try:
            return json.loads(self.params)
        except json.JSONDecodeError:
            return {}

    def set_params(self, params: Dict[str, Any]):
        """设置参数"""
        import json
        self.params = json.dumps(params, ensure_ascii=False)

    def is_executable(self) -> bool:
        """检查任务是否可执行"""
        return self.status in [TaskStatus.PENDING, TaskStatus.RUNNING]

    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status == TaskStatus.RUNNING

    def is_repeat_task(self) -> bool:
        """检查是否为重复任务"""
        return self.task_type != TaskType.ONCE
