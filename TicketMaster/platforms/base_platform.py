"""
平台基类模块
定义所有抢票平台的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
import random

from models import Account


@dataclass
class TicketInfo:
    """票务信息"""
    id: str
    name: str
    price: str
    stock: int  # 库存数量
    status: str  # 状态（有票、无票、待开售等）
    extra: Dict[str, Any] = None  # 额外信息

    def is_available(self) -> bool:
        """检查是否有票"""
        return self.stock > 0 and self.status in ['有票', '可订', '可购']


@dataclass
class OrderResult:
    """订单结果"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    error: str = ""
    extra: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'order_id': self.order_id,
            'message': self.message,
            'error': self.error,
            'extra': self.extra
        }


class BasePlatform(ABC):
    """平台基类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化平台

        Args:
            config: 平台配置
        """
        self.config = config or {}
        self.account: Optional[Account] = None
        self.is_logged_in = False
        self.session = None
        self.cookies = {}

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        获取平台名称

        Returns:
            平台名称
        """
        pass

    @abstractmethod
    def get_platform_code(self) -> str:
        """
        获取平台代码

        Returns:
            平台代码
        """
        pass

    @abstractmethod
    def login(self, account: Account) -> bool:
        """
        登录账号

        Args:
            account: 账号对象

        Returns:
            是否登录成功
        """
        pass

    @abstractmethod
    def logout(self) -> bool:
        """
        登出账号

        Returns:
            是否登出成功
        """
        pass

    @abstractmethod
    def check_login_status(self) -> bool:
        """
        检查登录状态

        Returns:
            是否已登录
        """
        pass

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        获取账号信息

        Returns:
            账号信息字典
        """
        return None

    # ==================== 搜索和查询 ====================

    @abstractmethod
    def search(self, params: Dict[str, Any]) -> List[TicketInfo]:
        """
        搜索票务信息

        Args:
            params: 搜索参数

        Returns:
            票务信息列表
        """
        pass

    @abstractmethod
    def check_stock(self, ticket_id: str) -> int:
        """
        检查票务库存

        Args:
            ticket_id: 票务 ID

        Returns:
            库存数量
        """
        pass

    # ==================== 订单操作 ====================

    @abstractmethod
    def order(self, ticket_id: str, params: Dict[str, Any] = None) -> OrderResult:
        """
        下单

        Args:
            ticket_id: 票务 ID
            params: 额外参数

        Returns:
            订单结果
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        获取订单状态

        Args:
            order_id: 订单 ID

        Returns:
            订单状态信息
        """
        pass

    # ==================== 辅助方法 ====================

    def set_account(self, account: Account):
        """
        设置账号

        Args:
            account: 账号对象
        """
        self.account = account

    def get_random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0) -> float:
        """
        获取随机延迟时间

        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）

        Returns:
            随机延迟时间
        """
        return random.uniform(min_delay, max_delay)

    def delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """
        随机延迟

        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        delay_time = self.get_random_delay(min_delay, max_delay)
        time.sleep(delay_time)

    def retry(self, func, max_times: int = 3, delay: float = 1.0):
        """
        重试装饰器

        Args:
            func: 要执行的函数
            max_times: 最大重试次数
            delay: 重试间隔

        Returns:
            函数执行结果
        """
        for attempt in range(max_times):
            try:
                return func()
            except Exception as e:
                if attempt == max_times - 1:
                    raise e
                time.sleep(delay)

    def get_user_agent(self) -> str:
        """
        获取随机 User-Agent

        Returns:
            User-Agent 字符串
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
        return random.choice(user_agents)

    def save_cookies(self):
        """保存 cookies"""
        if self.session:
            cookies_dict = self.session.cookies.get_dict()
            self.cookies = cookies_dict

    def load_cookies(self, cookies: Dict[str, str]):
        """
        加载 cookies

        Args:
            cookies: cookies 字典
        """
        self.cookies = cookies
        if self.session:
            for name, value in cookies.items():
                self.session.cookies.set(name, value)

    def close(self):
        """关闭资源"""
        if self.session:
            self.session.close()
            self.session = None
        self.is_logged_in = False
