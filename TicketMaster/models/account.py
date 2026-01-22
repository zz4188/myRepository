"""
数据模型模块
定义账号和任务的数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PlatformType(Enum):
    """平台类型枚举"""
    TICKET_12306 = "12306"
    DAMAI = "damai"
    CTRIP = "ctrip"

    @classmethod
    def from_string(cls, value: str) -> 'PlatformType':
        """从字符串创建枚举"""
        for platform in cls:
            if platform.value == value:
                return platform
        raise ValueError(f"未知的平台类型: {value}")

    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            PlatformType.TICKET_12306: "12306",
            PlatformType.DAMAI: "大麦网",
            PlatformType.CTRIP: "携程"
        }
        return names.get(self, self.value)


class AccountStatus(Enum):
    """账号状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOGIN_FAILED = "login_failed"
    EXPIRED = "expired"
    LOCKED = "locked"

    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            AccountStatus.ACTIVE: "正常",
            AccountStatus.INACTIVE: "未激活",
            AccountStatus.LOGIN_FAILED: "登录失败",
            AccountStatus.EXPIRED: "已过期",
            AccountStatus.LOCKED: "已锁定"
        }
        return names.get(self, self.value)


@dataclass
class Account:
    """账号数据模型"""
    id: Optional[int] = None
    platform: PlatformType = PlatformType.TICKET_12306
    username: str = ""
    password: str = ""  # 加密后的密码
    status: AccountStatus = AccountStatus.INACTIVE
    nickname: str = ""
    phone: str = ""
    email: str = ""
    cookies: str = ""  # 存储登录后的 cookies
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    remark: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform.value if isinstance(self.platform, PlatformType) else self.platform,
            'username': self.username,
            'password': self.password,
            'status': self.status.value if isinstance(self.status, AccountStatus) else self.status,
            'nickname': self.nickname,
            'phone': self.phone,
            'email': self.email,
            'cookies': self.cookies,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'remark': self.remark
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """从字典创建"""
        platform = data.get('platform', PlatformType.TICKET_12306.value)
        if isinstance(platform, str):
            platform = PlatformType.from_string(platform)

        status = data.get('status', AccountStatus.INACTIVE.value)
        if isinstance(status, str):
            try:
                status = AccountStatus(status)
            except ValueError:
                status = AccountStatus.INACTIVE

        return cls(
            id=data.get('id'),
            platform=platform,
            username=data.get('username', ''),
            password=data.get('password', ''),
            status=status,
            nickname=data.get('nickname', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            cookies=data.get('cookies', ''),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            remark=data.get('remark', '')
        )

    def is_available(self) -> bool:
        """检查账号是否可用"""
        return self.status == AccountStatus.ACTIVE
