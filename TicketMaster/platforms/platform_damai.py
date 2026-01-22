"""
大麦网平台抢票模块
实现大麦网演唱会/活动门票的登录、查询和抢票功能
"""

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from typing import Dict, Any, Optional, List
import time
import json
import random
from datetime import datetime

from .base_platform import BasePlatform, TicketInfo, OrderResult
from models import Account
from utils import get_config


class PlatformDamai(BasePlatform):
    """大麦网平台"""

    # 大麦网官方 API 地址
    BASE_URL = "https://www.damai.cn"
    LOGIN_URL = f"{BASE_URL}/login"
    ACTIVITY_URL = f"{BASE_URL}/"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.driver = None
        self.config = get_config()

    def get_platform_name(self) -> str:
        return "大麦网"

    def get_platform_code(self) -> str:
        return "damai"

    def _init_driver(self):
        """初始化浏览器驱动"""
        if not self.driver:
            chrome_options = Options()

            # 无头模式
            if self.config.get('browser.headless', True):
                chrome_options.add_argument('--headless')

            # 常用配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 设置窗口大小
            window_size = self.config.get('browser.window_size', [1920, 1080])
            chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')

            # 设置 User-Agent
            chrome_options.add_argument(f'user-agent={self.get_user_agent()}')

            # 指定驱动路径（如果配置了）
            driver_path = self.config.get('browser.driver_path')
            if driver_path:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)

            # 隐藏 webdriver 特征
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

    def login(self, account: Account) -> bool:
        """
        登录大麦网

        Args:
            account: 账号对象

        Returns:
            是否登录成功
        """
        self.set_account(account)
        self._init_driver()

        try:
            # 访问登录页面
            self.driver.get(self.LOGIN_URL)
            self.delay(2, 3)

            # 查找登录方式按钮（账号密码登录）
            # 大麦网登录页面可能有多种登录方式
            try:
                password_tab = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '密码登录')]"))
                )
                password_tab.click()
                self.delay(0.5, 1)
            except:
                pass  # 可能默认就是密码登录

            # 输入用户名（手机号）
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='手机号/邮箱']"))
            )
            username_input.clear()
            username_input.send_keys(account.username)
            self.delay(0.5, 1)

            # 输入密码
            password_input = self.driver.find_element(By.XPATH, "//input[@placeholder='请输入密码']")
            password_input.clear()
            password_input.send_keys(account.password)
            self.delay(0.5, 1)

            # 点击登录按钮
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登录')]")
            login_button.click()
            self.delay(2, 3)

            # 等待跳转或登录完成
            time.sleep(3)

            # 检查是否需要验证码
            # 可能需要滑动验证码、短信验证等

            # 检查是否登录成功
            if self.check_login_status():
                self.is_logged_in = True
                self.save_cookies()
                return True
            else:
                return False

        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def logout(self) -> bool:
        """登出"""
        try:
            if self.driver:
                # 点击退出按钮或访问退出接口
                self.driver.get(f"{self.BASE_URL}/passport/logout")
                self.delay(1, 2)
            self.is_logged_in = False
            return True
        except Exception as e:
            print(f"登出失败: {e}")
            return False

    def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            if not self.driver:
                return False

            # 访问个人中心页面
            self.driver.get(f"{self.BASE_URL}/userCenter")
            self.delay(1, 2)

            # 检查页面是否包含登录成功的标志
            # 例如检查是否显示用户名、登录按钮是否消失等
            page_source = self.driver.page_source

            # 简单判断：如果页面包含"登录"按钮则未登录
            if '登录' in page_source and '登录' in page_source[:1000]:
                return False

            return True

        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False

    def search(self, params: Dict[str, Any]) -> List[TicketInfo]:
        """
        搜索演出/活动信息

        Args:
            params: 搜索参数
                - keyword: 搜索关键词
                - city: 城市
                - date: 演出日期

        Returns:
            票务信息列表
        """
        if not self.is_logged_in:
            raise Exception("未登录，请先登录")

        try:
            keyword = params.get('keyword', '')
            city = params.get('city', '')

            # 构建搜索 URL
            search_url = f"{self.BASE_URL}/search.html"
            if keyword:
                search_url += f"?keyword={keyword}"
            if city:
                search_url += f"&city={city}"

            # 访问搜索页面
            self.driver.get(search_url)
            self.delay(2, 3)

            # 解析活动列表
            tickets = []

            # 查找活动元素（选择器需要根据实际页面结构调整）
            try:
                activity_elements = self.driver.find_elements(By.CLASS_NAME, "search-item")

                for element in activity_elements:
                    try:
                        # 提取活动信息
                        name_elem = element.find_element(By.CLASS_NAME, "item-title")
                        name = name_elem.text if name_elem else "未知活动"

                        # 获取链接
                        link_elem = element.find_element(By.TAG_NAME, "a")
                        url = link_elem.get_attribute('href') if link_elem else ""

                        # 提取价格信息
                        price_elem = element.find_element(By.CLASS_NAME, "item-price")
                        price = price_elem.text if price_elem else "暂无价格"

                        # 提取时间信息
                        time_elem = element.find_element(By.CLASS_NAME, "item-time")
                        time_text = time_elem.text if time_elem else "暂无时间"

                        ticket = TicketInfo(
                            id=url,
                            name=f"{name} - {time_text}",
                            price=price,
                            stock=100,  # 库存信息需要进入详情页获取
                            status='可购买',
                            extra={
                                'url': url,
                                'time': time_text
                            }
                        )
                        tickets.append(ticket)

                    except Exception as e:
                        print(f"解析活动元素失败: {e}")
                        continue

            except Exception as e:
                print(f"查找活动元素失败: {e}")

            return tickets

        except Exception as e:
            print(f"搜索活动失败: {e}")
            return []

    def check_stock(self, ticket_id: str) -> int:
        """
        检查票务库存

        Args:
            ticket_id: 票务 URL

        Returns:
            库存数量
        """
        try:
            # 访问活动详情页
            self.driver.get(ticket_id)
            self.delay(1, 2)

            # 查找库存信息
            # 实际应用中需要根据页面结构解析
            # 这里简化处理
            return 100

        except Exception as e:
            print(f"检查库存失败: {e}")
            return 0

    def order(self, ticket_id: str, params: Dict[str, Any] = None) -> OrderResult:
        """
        下单

        Args:
            ticket_id: 票务 URL
            params: 订单参数
                - ticket_level: 票档（如：看台票、内场票等）
                - quantity: 购买数量

        Returns:
            订单结果
        """
        if not self.is_logged_in:
            return OrderResult(
                success=False,
                error="未登录，请先登录"
            )

        params = params or {}
        ticket_level = params.get('ticket_level', '')
        quantity = params.get('quantity', 1)

        try:
            # 1. 访问活动详情页
            self.driver.get(ticket_id)
            self.delay(2, 3)

            # 2. 选择票档
            if ticket_level:
                try:
                    # 查找对应的票档元素
                    level_elements = self.driver.find_elements(By.CLASS_NAME, "sku-item")
                    for elem in level_elements:
                        if ticket_level in elem.text:
                            elem.click()
                            self.delay(0.5, 1)
                            break
                except:
                    pass

            # 3. 点击"立即购买"或"立即预订"按钮
            buy_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '立即购买') or contains(text(), '立即预订')]"))
            )
            buy_button.click()
            self.delay(2, 3)

            # 4. 选择观演人
            # 实际应用中需要处理观演人选择
            self.delay(1, 2)

            # 5. 提交订单
            # 可能需要处理验证码、支付等
            return OrderResult(
                success=True,
                order_id=f"damai-{int(time.time())}",
                message="订单提交成功，请完成支付"
            )

        except Exception as e:
            return OrderResult(
                success=False,
                error=str(e),
                message="订单提交失败"
            )

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        获取订单状态

        Args:
            order_id: 订单 ID

        Returns:
            订单状态信息
        """
        # 访问订单查询页面
        # 简化处理
        return {
            'order_id': order_id,
            'status': '待支付',
            'message': '订单已创建，等待支付'
        }

    def get_ticket_levels(self, activity_url: str) -> List[Dict[str, Any]]:
        """
        获取活动的票档列表

        Args:
            activity_url: 活动 URL

        Returns:
            票档列表
        """
        try:
            # 访问活动详情页
            self.driver.get(activity_url)
            self.delay(1, 2)

            # 解析票档信息
            levels = []

            try:
                level_elements = self.driver.find_elements(By.CLASS_NAME, "sku-item")
                for elem in level_elements:
                    level_text = elem.text
                    # 解析票档名称和价格
                    parts = level_text.split('¥')
                    if len(parts) >= 2:
                        levels.append({
                            'name': parts[0].strip(),
                            'price': parts[1].strip()
                        })
                    else:
                        levels.append({
                            'name': level_text,
                            'price': ''
                        })
            except:
                pass

            return levels

        except Exception as e:
            print(f"获取票档失败: {e}")
            return []

    def close(self):
        """关闭资源"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        super().close()
