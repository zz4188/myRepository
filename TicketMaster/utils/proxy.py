"""
代理管理工具模块
支持 HTTP/SOCKS5 代理配置和管理
"""

import random
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class Proxy:
    """代理信息"""
    type: str  # 'http', 'https', 'socks5'
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            'type': self.type,
            'host': self.host,
            'port': self.port
        }
        if self.username and self.password:
            result['username'] = self.username
            result['password'] = self.password
        return result

    def to_url(self) -> str:
        """转换为代理 URL"""
        if self.username and self.password:
            return f"{self.type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.type}://{self.host}:{self.port}"

    @classmethod
    def from_dict(cls, data: dict) -> 'Proxy':
        """从字典创建 Proxy"""
        return cls(
            type=data['type'],
            host=data['host'],
            port=data['port'],
            username=data.get('username'),
            password=data.get('password')
        )


class ProxyManager:
    """代理管理器"""

    def __init__(self):
        self._proxies: List[Proxy] = []
        self._current_index = 0
        self._use_rotation = False
        self._use_random = False

    def add_proxy(self, proxy: Proxy):
        """
        添加代理

        Args:
            proxy: 代理对象
        """
        if proxy not in self._proxies:
            self._proxies.append(proxy)

    def add_proxies(self, proxies: List[Proxy]):
        """
        批量添加代理

        Args:
            proxies: 代理列表
        """
        for proxy in proxies:
            self.add_proxy(proxy)

    def remove_proxy(self, proxy: Proxy):
        """
        移除代理

        Args:
            proxy: 要移除的代理
        """
        if proxy in self._proxies:
            self._proxies.remove(proxy)

    def clear_proxies(self):
        """清空所有代理"""
        self._proxies.clear()
        self._current_index = 0

    def get_proxy(self) -> Optional[Proxy]:
        """
        获取一个代理

        Returns:
            代理对象，如果没有代理则返回 None
        """
        if not self._proxies:
            return None

        if self._use_random:
            return random.choice(self._proxies)
        elif self._use_rotation:
            proxy = self._proxies[self._current_index % len(self._proxies)]
            self._current_index += 1
            return proxy
        else:
            return self._proxies[0]

    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """
        获取代理字典格式（用于 requests）

        Returns:
            代理字典，例如 {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
        """
        proxy = self.get_proxy()
        if not proxy:
            return None

        url = proxy.to_url()
        return {
            'http': url,
            'https': url
        }

    def get_proxies(self) -> List[Proxy]:
        """
        获取所有代理

        Returns:
            代理列表
        """
        return self._proxies.copy()

    def set_rotation_mode(self, enabled: bool = True):
        """
        设置轮询模式

        Args:
            enabled: 是否启用轮询
        """
        self._use_rotation = enabled
        self._use_random = False

    def set_random_mode(self, enabled: bool = True):
        """
        设置随机模式

        Args:
            enabled: 是否启用随机
        """
        self._use_random = enabled
        self._use_rotation = False

    def get_count(self) -> int:
        """
        获取代理数量

        Returns:
            代理数量
        """
        return len(self._proxies)

    def is_enabled(self) -> bool:
        """
        检查代理是否启用

        Returns:
            是否有可用代理
        """
        return len(self._proxies) > 0

    def validate_proxy(self, proxy: Proxy, timeout: int = 5) -> bool:
        """
        验证代理是否可用

        Args:
            proxy: 代理对象
            timeout: 超时时间（秒）

        Returns:
            代理是否可用
        """
        import requests
        try:
            proxy_dict = {
                'http': proxy.to_url(),
                'https': proxy.to_url()
            }
            response = requests.get(
                'http://www.baidu.com',
                proxies=proxy_dict,
                timeout=timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    def load_from_file(self, filepath: str):
        """
        从文件加载代理

        Args:
            filepath: 文件路径
        """
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        self.add_proxy(Proxy.from_dict(item))
        except Exception as e:
            print(f"加载代理文件失败: {e}")

    def save_to_file(self, filepath: str):
        """
        保存代理到文件

        Args:
            filepath: 文件路径
        """
        import json
        try:
            data = [proxy.to_dict() for proxy in self._proxies]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存代理文件失败: {e}")


# 创建全局代理管理器实例
_default_proxy_manager = None


def get_proxy_manager() -> ProxyManager:
    """
    获取全局代理管理器实例

    Returns:
        ProxyManager 实例
    """
    global _default_proxy_manager
    if _default_proxy_manager is None:
        _default_proxy_manager = ProxyManager()
    return _default_proxy_manager
