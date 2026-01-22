"""
数据模型模块初始化
"""
from .account import Account, PlatformType, AccountStatus
from .task import Task, TaskStatus, TaskType

__all__ = [
    'Account', 'PlatformType', 'AccountStatus',
    'Task', 'TaskStatus', 'TaskType'
]
