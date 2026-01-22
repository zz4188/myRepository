"""
配置管理工具模块
负责应用程序的配置加载、保存和管理
"""

import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """配置管理器"""

    # 默认配置
    DEFAULT_CONFIG = {
        # 通用设置
        'app_name': 'TicketMaster',
        'version': '1.0.0',
        'language': 'zh_CN',

        # 代理设置
        'proxy': {
            'enabled': False,
            'type': 'http',  # http, https, socks5
            'host': '',
            'port': 8080,
            'username': '',
            'password': ''
        },

        # 请求设置
        'request': {
            'timeout': 30,
            'retry_times': 3,
            'retry_delay': 1.0,
            'min_delay': 0.5,
            'max_delay': 2.0
        },

        # 抢票设置
        'ticket': {
            'auto_retry': True,
            'check_interval': 1.0,  # 检查间隔（秒）
            'max_duration': 300,   # 最大抢票时长（秒）
            'order_timeout': 60    # 下单超时（秒）
        },

        # 浏览器设置
        'browser': {
            'type': 'chrome',  # chrome, firefox, edge
            'headless': True,
            'driver_path': '',  # 留空则自动查找
            'window_size': [1920, 1080],
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },

        # 日志设置
        'logging': {
            'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            'console_output': True,
            'file_output': True,
            'log_dir': 'logs',
            'max_file_size': 10485760,  # 10MB
            'backup_count': 5,
            'retention_days': 30
        },

        # 数据库设置
        'database': {
            'path': 'data/ticketmaster.db'
        },

        # 定时任务设置
        'scheduler': {
            'max_workers': 5,
            'timezone': 'Asia/Shanghai'
        },

        # 通知设置
        'notification': {
            'enabled': True,
            'sound': True,
            'popup': True
        }
    }

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，如果为 None 则使用默认目录
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 使用应用数据目录
            if os.name == 'nt':  # Windows
                self.config_dir = Path(os.path.expanduser('~/AppData/Local/TicketMaster'))
            else:  # Linux/Mac
                self.config_dir = Path(os.path.expanduser('~/.ticketmaster'))

        self.config_file = self.config_dir / 'config.json'
        self._config: Dict[str, Any] = {}

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.load()

    def load(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # 合并默认配置（确保所有配置项都存在）
                self._config = self._deep_merge(self.DEFAULT_CONFIG, self._config)
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'proxy.enabled'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, save: bool = True):
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
            save: 是否立即保存
        """
        keys = key.split('.')
        config = self._config

        # 导航到最后一层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

        if save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            完整的配置字典
        """
        return self._config.copy()

    def reset(self, save: bool = True):
        """
        重置为默认配置

        Args:
            save: 是否立即保存
        """
        self._config = self.DEFAULT_CONFIG.copy()
        if save:
            self.save()

    def _deep_merge(self, default: dict, user: dict) -> dict:
        """
        深度合并字典（以 default 为基准，用 user 的值覆盖）

        Args:
            default: 默认配置
            user: 用户配置

        Returns:
            合并后的配置
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def update(self, config: Dict[str, Any], save: bool = True):
        """
        批量更新配置

        Args:
            config: 要更新的配置字典
            save: 是否立即保存
        """
        self._config = self._deep_merge(self._config, config)
        if save:
            self.save()

    def export(self, filepath: str):
        """
        导出配置到文件

        Args:
            filepath: 导出文件路径
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"导出配置失败: {e}")

    def import_config(self, filepath: str, save: bool = True):
        """
        从文件导入配置

        Args:
            filepath: 配置文件路径
            save: 是否立即保存
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.update(config, save)
        except Exception as e:
            print(f"导入配置失败: {e}")

    def get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """
        获取代理配置

        Returns:
            代理配置字典，如果未启用则返回 None
        """
        if not self.get('proxy.enabled', False):
            return None

        proxy_config = self.get('proxy')
        return proxy_config

    def is_proxy_enabled(self) -> bool:
        """
        检查代理是否启用

        Returns:
            代理是否启用
        """
        return self.get('proxy.enabled', False)

    def get_log_dir(self) -> Path:
        """
        获取日志目录

        Returns:
            日志目录路径
        """
        log_dir = self.config_dir / self.get('logging.log_dir', 'logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def get_database_path(self) -> Path:
        """
        获取数据库文件路径

        Returns:
            数据库文件路径
        """
        db_path = self.config_dir / self.get('database.path', 'data/ticketmaster.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path


# 创建全局配置实例
_default_config = None


def get_config(config_dir: str = None) -> Config:
    """
    获取全局配置实例

    Args:
        config_dir: 配置文件目录

    Returns:
        Config 实例
    """
    global _default_config
    if _default_config is None:
        _default_config = Config(config_dir)
    return _default_config
