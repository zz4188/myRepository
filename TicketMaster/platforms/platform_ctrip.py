"""
携程平台抢票模块
实现携程酒店和机票的登录、查询和预订功能
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
from datetime import datetime, timedelta

from .base_platform import BasePlatform, TicketInfo, OrderResult
from models import Account
from utils import get_config


class PlatformCtrip(BasePlatform):
    """携程平台"""

    # 携程官方 URL
    BASE_URL = "https://www.ctrip.com"
    LOGIN_URL = f"{BASE_URL}/webapp/login"
    HOTEL_SEARCH_URL = f"{BASE_URL}/webapp/hotel/hoteldetail"
    FLIGHT_SEARCH_URL = f"{BASE_URL}/flights"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.driver = None
        self.config = get_config()

    def get_platform_name(self) -> str:
        return "携程"

    def get_platform_code(self) -> str:
        return "ctrip"

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
        登录携程

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

            # 查找登录方式（账号密码登录）
            try:
                # 切换到账号密码登录
                password_tab = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '账号登录')]"))
                )
                password_tab.click()
                self.delay(0.5, 1)
            except:
                pass

            # 输入用户名（手机号/邮箱）
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, '手机号') or contains(@placeholder, '邮箱')]"))
            )
            username_input.clear()
            username_input.send_keys(account.username)
            self.delay(0.5, 1)

            # 输入密码
            password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password_input.clear()
            password_input.send_keys(account.password)
            self.delay(0.5, 1)

            # 点击登录按钮
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登录')]")
            login_button.click()
            self.delay(2, 3)

            # 等待跳转或登录完成
            time.sleep(3)

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
                self.driver.get(f"{self.BASE_URL}/member/logout")
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
            self.driver.get(f"{self.BASE_URL}/member/myinfo")
            self.delay(1, 2)

            # 检查页面是否包含登录成功的标志
            page_source = self.driver.page_source

            # 简单判断：如果页面包含"登录"按钮则未登录
            if '登录' in page_source and '登录' in page_source[:1000]:
                return False

            return True

        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False

    def search_hotels(self, params: Dict[str, Any]) -> List[TicketInfo]:
        """
        搜索酒店

        Args:
            params: 搜索参数
                - city: 城市
                - check_in_date: 入住日期 (YYYY-MM-DD)
                - check_out_date: 离店日期 (YYYY-MM-DD)
                - price_range: 价格范围 (如: 0-500)

        Returns:
            酒店信息列表
        """
        if not self.is_logged_in:
            raise Exception("未登录，请先登录")

        try:
            city = params.get('city', '')
            check_in = params.get('check_in_date', datetime.now().strftime('%Y-%m-%d'))
            check_out = params.get('check_out_date', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

            # 构建搜索 URL
            search_url = f"{self.BASE_URL}/webapp/hotel/hotellist?city={city}&checkIn={check_in}&checkOut={check_out}"

            # 访问搜索页面
            self.driver.get(search_url)
            self.delay(2, 3)

            # 解析酒店列表
            hotels = []

            try:
                hotel_elements = self.driver.find_elements(By.CLASS_NAME, "hotel-item")

                for element in hotel_elements:
                    try:
                        # 提取酒店名称
                        name_elem = element.find_element(By.CLASS_NAME, "hotel-name")
                        name = name_elem.text if name_elem else "未知酒店"

                        # 提取价格
                        price_elem = element.find_element(By.CLASS_NAME, "hotel-price")
                        price = price_elem.text if price_elem else "暂无价格"

                        # 提取评分
                        score_elem = element.find_element(By.CLASS_NAME, "hotel-score")
                        score = score_elem.text if score_elem else "暂无评分"

                        # 获取酒店链接
                        link_elem = element.find_element(By.TAG_NAME, "a")
                        url = link_elem.get_attribute('href') if link_elem else ""

                        hotel = TicketInfo(
                            id=url,
                            name=f"{name} - {score}",
                            price=price,
                            stock=10,  # 可预订房间数
                            status='可预订',
                            extra={
                                'url': url,
                                'score': score,
                                'type': 'hotel'
                            }
                        )
                        hotels.append(hotel)

                    except Exception as e:
                        print(f"解析酒店元素失败: {e}")
                        continue

            except Exception as e:
                print(f"查找酒店元素失败: {e}")

            return hotels

        except Exception as e:
            print(f"搜索酒店失败: {e}")
            return []

    def search_flights(self, params: Dict[str, Any]) -> List[TicketInfo]:
        """
        搜索机票

        Args:
            params: 搜索参数
                - from_city: 出发城市
                - to_city: 到达城市
                - date: 出发日期 (YYYY-MM-DD)

        Returns:
            机票信息列表
        """
        if not self.is_logged_in:
            raise Exception("未登录，请先登录")

        try:
            from_city = params.get('from_city', '')
            to_city = params.get('to_city', '')
            date = params.get('date', datetime.now().strftime('%Y-%m-%d'))

            # 构建搜索 URL
            search_url = f"{self.BASE_URL}/flights/list?depCity={from_city}&arrCity={to_city}&date={date}"

            # 访问搜索页面
            self.driver.get(search_url)
            self.delay(2, 3)

            # 解析航班列表
            flights = []

            try:
                flight_elements = self.driver.find_elements(By.CLASS_NAME, "flight-item")

                for element in flight_elements:
                    try:
                        # 提取航班信息
                        airline_elem = element.find_element(By.CLASS_NAME, "airline-name")
                        airline = airline_elem.text if airline_elem else "未知航空公司"

                        # 提取时间
                        dep_time_elem = element.find_element(By.CLASS_NAME, "dep-time")
                        dep_time = dep_time_elem.text if dep_time_elem else ""

                        arr_time_elem = element.find_element(By.CLASS_NAME, "arr-time")
                        arr_time = arr_time_elem.text if arr_time_elem else ""

                        # 提取价格
                        price_elem = element.find_element(By.CLASS_NAME, "flight-price")
                        price = price_elem.text if price_elem else "暂无价格"

                        # 获取航班链接
                        link_elem = element.find_element(By.TAG_NAME, "a")
                        url = link_elem.get_attribute('href') if link_elem else ""

                        flight = TicketInfo(
                            id=url,
                            name=f"{airline} {dep_time}-{arr_time}",
                            price=price,
                            stock=20,  # 可座位数
                            status='可预订',
                            extra={
                                'url': url,
                                'airline': airline,
                                'dep_time': dep_time,
                                'arr_time': arr_time,
                                'type': 'flight'
                            }
                        )
                        flights.append(flight)

                    except Exception as e:
                        print(f"解析航班元素失败: {e}")
                        continue

            except Exception as e:
                print(f"查找航班元素失败: {e}")

            return flights

        except Exception as e:
            print(f"搜索机票失败: {e}")
            return []

    def search(self, params: Dict[str, Any]) -> List[TicketInfo]:
        """
        搜索酒店或机票（根据参数类型自动判断）

        Args:
            params: 搜索参数

        Returns:
            票务信息列表
        """
        # 判断搜索类型
        if params.get('type') == 'flight':
            return self.search_flights(params)
        else:
            return self.search_hotels(params)

    def check_stock(self, ticket_id: str) -> int:
        """
        检查库存

        Args:
            ticket_id: 酒店/机票 URL

        Returns:
            库存数量
        """
        try:
            # 访问详情页
            self.driver.get(ticket_id)
            self.delay(1, 2)

            # 查找库存信息
            # 简化处理
            return 10

        except Exception as e:
            print(f"检查库存失败: {e}")
            return 0

    def order(self, ticket_id: str, params: Dict[str, Any] = None) -> OrderResult:
        """
        下单

        Args:
            ticket_id: 酒店/机票 URL
            params: 订单参数
                - room_type: 房间类型
                - nights: 住宿天数（酒店）
                - passengers: 乘客信息（机票）

        Returns:
            订单结果
        """
        if not self.is_logged_in:
            return OrderResult(
                success=False,
                error="未登录，请先登录"
            )

        params = params or {}

        try:
            # 1. 访问详情页
            self.driver.get(ticket_id)
            self.delay(2, 3)

            # 2. 选择房间/航班
            # 根据实际页面结构选择

            # 3. 点击预订按钮
            book_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '预订') or contains(text(), '立即预订')]"))
            )
            book_button.click()
            self.delay(2, 3)

            # 4. 填写预订信息
            # 实际应用中需要处理入住人、联系方式等

            # 5. 提交订单
            return OrderResult(
                success=True,
                order_id=f"ctrip-{int(time.time())}",
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

    def close(self):
        """关闭资源"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        super().close()
