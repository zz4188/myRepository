"""
日志系统模块
提供统一的日志记录功能，支持控制台输出、文件输出、数据库存储
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

try:
    from colorlog import ColoredFormatter
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

from utils import get_config


class Logger:
    """日志管理器"""

    # 日志级别映射
    LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self, name: str = 'TicketMaster', db=None):
        """
        初始化日志管理器

        Args:
            name: 日志器名称
            db: 数据库实例（用于存储日志到数据库）
        """
        self.name = name
        self.db = db
        self.logger = logging.getLogger(name)
        self.logger.handlers.clear()

        # 加载配置
        self.config = get_config()
        self.level = self.config.get('logging.level', 'INFO')

        # 设置日志级别
        self.logger.setLevel(self.LEVEL_MAP.get(self.level, logging.INFO))

        # 配置处理器
        self._setup_handlers()

    def _setup_handlers(self):
        """配置日志处理器"""
        # 控制台输出
        if self.config.get('logging.console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.logger.level)

            if HAS_COLORLOG:
                # 彩色输出
                formatter = ColoredFormatter(
                    '%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            else:
                # 普通输出
                formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )

            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件输出
        if self.config.get('logging.file_output', True):
            log_dir = self.config.get_log_dir()
            log_file = log_dir / f'ticketmaster_{datetime.now().strftime("%Y%m%d")}.log'

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(self.logger.level)

            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _add_to_database(self, level: str, message: str,
                        task_id: int = None, account_id: int = None,
                        platform: str = None, extra_data: dict = None):
        """
        添加日志到数据库

        Args:
            level: 日志级别
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        if self.db:
            try:
                self.db.add_log(
                    level=level,
                    message=message,
                    task_id=task_id,
                    account_id=account_id,
                    platform=platform,
                    extra_data=extra_data
                )
            except Exception as e:
                self.logger.error(f"写入数据库日志失败: {e}")

    def debug(self, message: str, task_id: int = None, account_id: int = None,
              platform: str = None, extra_data: dict = None):
        """
        记录 DEBUG 级别日志

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        self.logger.debug(message)
        self._add_to_database('DEBUG', message, task_id, account_id, platform, extra_data)

    def info(self, message: str, task_id: int = None, account_id: int = None,
             platform: str = None, extra_data: dict = None):
        """
        记录 INFO 级别日志

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        self.logger.info(message)
        self._add_to_database('INFO', message, task_id, account_id, platform, extra_data)

    def warning(self, message: str, task_id: int = None, account_id: int = None,
                platform: str = None, extra_data: dict = None):
        """
        记录 WARNING 级别日志

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        self.logger.warning(message)
        self._add_to_database('WARNING', message, task_id, account_id, platform, extra_data)

    def error(self, message: str, task_id: int = None, account_id: int = None,
              platform: str = None, extra_data: dict = None, exception: Exception = None):
        """
        记录 ERROR 级别日志

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
            exception: 异常对象
        """
        if exception:
            message = f"{message} - {str(exception)}"
        self.logger.error(message)
        self._add_to_database('ERROR', message, task_id, account_id, platform, extra_data)

    def success(self, message: str, task_id: int = None, account_id: int = None,
                platform: str = None, extra_data: dict = None):
        """
        记录 SUCCESS 级别日志（特殊级别）

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        self.logger.info(f"✓ {message}")
        self._add_to_database('SUCCESS', message, task_id, account_id, platform, extra_data)

    def critical(self, message: str, task_id: int = None, account_id: int = None,
                 platform: str = None, extra_data: dict = None):
        """
        记录 CRITICAL 级别日志

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        self.logger.critical(message)
        self._add_to_database('CRITICAL', message, task_id, account_id, platform, extra_data)

    def exception(self, message: str, task_id: int = None, account_id: int = None,
                 platform: str = None, extra_data: dict = None):
        """
        记录异常日志（自动包含堆栈信息）

        Args:
            message: 日志消息
            task_id: 关联任务 ID
            account_id: 关联账号 ID
            platform: 平台类型
            extra_data: 额外数据
        """
        self.logger.exception(message)
        self._add_to_database('ERROR', message, task_id, account_id, platform, extra_data)

    def set_level(self, level: str):
        """
        设置日志级别

        Args:
            level: 日志级别字符串（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        self.level = level.upper()
        self.logger.setLevel(self.LEVEL_MAP.get(self.level, logging.INFO))

        for handler in self.logger.handlers:
            handler.setLevel(self.LEVEL_MAP.get(self.level, logging.INFO))


# 创建全局日志实例
_default_logger = None


def get_logger(name: str = 'TicketMaster', db=None) -> Logger:
    """
    获取全局日志实例

    Args:
        name: 日志器名称
        db: 数据库实例

    Returns:
        Logger 实例
    """
    global _default_logger
    if _default_logger is None or db is not None:
        _default_logger = Logger(name, db)
    return _default_logger
