"""
平台模块初始化
"""
from .base_platform import BasePlatform
from .platform_12306 import Platform12306
from .platform_damai import PlatformDamai
from .platform_ctrip import PlatformCtrip

__all__ = ['BasePlatform', 'Platform12306', 'PlatformDamai', 'PlatformCtrip']
