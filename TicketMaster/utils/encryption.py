"""
加密工具模块
使用 cryptography 库提供密码加密/解密功能
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class Encryption:
    """加密/解密工具类"""

    def __init__(self, master_key: str = None):
        """
        初始化加密工具

        Args:
            master_key: 主密钥，如果为 None 则生成新密钥
        """
        if master_key:
            self.key = self._derive_key(master_key)
        else:
            # 从环境变量或配置文件读取密钥
            env_key = os.getenv('TICKETMASTER_KEY')
            if env_key:
                self.key = env_key.encode()
            else:
                # 如果没有密钥，使用固定的设备特定密钥
                # 在实际应用中应该从安全配置文件中读取
                self.key = b'TicketMaster-Secret-Key-2024-For-Encryption'
                if len(self.key) != 32:
                    self.key = self.key.ljust(32, b'0')[:32]

        # 确保 key 是 32 字节（256 位）
        if len(self.key) != 32:
            # 使用 PBKDF2 派生密钥
            self.key = self._derive_key(str(self.key))

        # 使用 base64 编码的密钥
        self.fernet = Fernet(base64.urlsafe_b64encode(self.key))

    def _derive_key(self, password: str) -> bytes:
        """
        从密码派生密钥

        Args:
            password: 密码

        Returns:
            32 字节的密钥
        """
        salt = b'TicketMaster-Salt-2024'  # 在生产环境应使用随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        加密文本

        Args:
            plaintext: 明文

        Returns:
            加密后的文本（base64 编码）
        """
        if not plaintext:
            return ''
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        解密文本

        Args:
            ciphertext: 加密的文本（base64 编码）

        Returns:
            解密后的明文
        """
        if not ciphertext:
            return ''
        try:
            decrypted = self.fernet.decrypt(base64.urlsafe_b64decode(ciphertext.encode()))
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")

    def encrypt_dict(self, data: dict) -> dict:
        """
        加密字典中的所有字符串值

        Args:
            data: 要加密的字典

        Returns:
            加密后的字典
        """
        encrypted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_data[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted_data[key] = self.encrypt_dict(value)
            elif isinstance(value, list):
                encrypted_data[key] = [self.encrypt(item) if isinstance(item, str) else item for item in value]
            else:
                encrypted_data[key] = value
        return encrypted_data

    def decrypt_dict(self, data: dict) -> dict:
        """
        解密字典中的所有字符串值

        Args:
            data: 要解密的字典

        Returns:
            解密后的字典
        """
        decrypted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    decrypted_data[key] = self.decrypt(value)
                except ValueError:
                    decrypted_data[key] = value  # 解密失败则保留原值
            elif isinstance(value, dict):
                decrypted_data[key] = self.decrypt_dict(value)
            elif isinstance(value, list):
                decrypted_list = []
                for item in value:
                    if isinstance(item, str):
                        try:
                            decrypted_list.append(self.decrypt(item))
                        except ValueError:
                            decrypted_list.append(item)
                    else:
                        decrypted_list.append(item)
                decrypted_data[key] = decrypted_list
            else:
                decrypted_data[key] = value
        return decrypted_data

    def generate_key(self) -> str:
        """
        生成新的加密密钥

        Returns:
            base64 编码的密钥字符串
        """
        return base64.urlsafe_b64encode(os.urandom(32)).decode()

    def validate_key(self, key: str) -> bool:
        """
        验证密钥是否有效

        Args:
            key: 要验证的密钥

        Returns:
            密钥是否有效
        """
        try:
            # 尝试使用密钥创建 Fernet 实例
            fernet = Fernet(key)
            # 尝试加密和解密
            test_data = "test"
            encrypted = fernet.encrypt(test_data.encode())
            decrypted = fernet.decrypt(encrypted).decode()
            return decrypted == test_data
        except Exception:
            return False


# 创建全局加密实例
_default_encryption = None


def get_encryption() -> Encryption:
    """
    获取全局加密实例

    Returns:
        Encryption 实例
    """
    global _default_encryption
    if _default_encryption is None:
        _default_encryption = Encryption()
    return _default_encryption
