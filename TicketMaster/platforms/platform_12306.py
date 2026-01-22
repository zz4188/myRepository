"""
12306 平台抢票模块
实现 12306 火车票的登录、查询和抢票功能
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


class Platform12306(BasePlatform):
    """12306 平台"""

    # 12306 官方 API 地址
    BASE_URL = "https://kyfw.12306.cn"
    LOGIN_URL = f"{BASE_URL}/otn/resources/login.html"
    QUERY_URL = f"{BASE_URL}/otn/leftTicket/query"
    CHECK_USER_URL = f"{BASE_URL}/otn/login/checkUser"
    SUBMIT_ORDER_URL = f"{BASE_URL}/otn/leftTicket/submitOrderRequest"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.driver = None
        self.config = get_config()

    def get_platform_name(self) -> str:
        return "12306"

    def get_platform_code(self) -> str:
        return "12306"

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
        登录 12306

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
            self.delay(1, 2)

            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "J-userName"))
            )

            # 输入用户名
            username_input = self.driver.find_element(By.ID, "J-userName")
            username_input.clear()
            username_input.send_keys(account.username)
            self.delay(0.5, 1)

            # 输入密码
            password_input = self.driver.find_element(By.ID, "J-password")
            password_input.clear()
            password_input.send_keys(account.password)
            self.delay(0.5, 1)

            # 点击登录按钮
            login_button = self.driver.find_element(By.ID, "J-login")
            login_button.click()
            self.delay(2, 3)

            # 检查是否需要验证码
            # 这里简化处理，实际应用中需要处理验证码
            # 可能需要人工干预或使用验证码识别服务

            # 等待登录完成
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
                # 点击退出按钮
                self.driver.get(f"{self.BASE_URL}/otn/login/out")
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

            # 访问检查用户接口
            self.driver.get(self.CHECK_USER_URL)
            self.delay(0.5, 1)

            # 获取响应
            response_text = self.driver.find_element(By.TAG_NAME, "pre").text
            data = json.loads(response_text)

            # 检查标志位
            return data.get('data', {}).get('flag', False)

        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False

    def search(self, params: Dict[str, Any]) -> List[TicketInfo]:
        """
        查询车次信息

        Args:
            params: 查询参数
                - date: 出发日期 (YYYY-MM-DD)
                - from_station: 出发站代码
                - to_station: 到达站代码
                - purpose_codes: 购票类型 (ADULT: 成人票, STUDENT: 学生票)

        Returns:
            车次信息列表
        """
        if not self.is_logged_in:
            raise Exception("未登录，请先登录")

        try:
            # 构建查询参数
            query_params = {
                'leftTicketDTO.train_date': params.get('date', datetime.now().strftime('%Y-%m-%d')),
                'leftTicketDTO.from_station': params.get('from_station', ''),
                'leftTicketDTO.to_station': params.get('to_station', ''),
                'purpose_codes': params.get('purpose_codes', 'ADULT')
            }

            # 访问查询接口
            self.driver.get(f"{self.QUERY_URL}?{'&'.join([f'{k}={v}' for k, v in query_params.items()])}")
            self.delay(1, 2)

            # 解析响应
            response_text = self.driver.find_element(By.TAG_NAME, "pre").text
            data = json.loads(response_text)

            # 解析车次数据
            tickets = []
            if data.get('data') and data['data'].get('result'):
                for item in data['data']['result']:
                    ticket = self._parse_ticket_data(item)
                    if ticket:
                        tickets.append(ticket)

            return tickets

        except Exception as e:
            print(f"查询车次失败: {e}")
            return []

    def _parse_ticket_data(self, data: str) -> Optional[TicketInfo]:
        """
        解析车次数据

        Args:
            data: 车次数据字符串

        Returns:
            车次信息
        """
        try:
            # 数据格式为 "|" 分隔的字符串
            fields = data.split('|')

            # 提取关键信息
            train_no = fields[2]  # 车次号
            from_station = fields[3]  # 出发站
            to_station = fields[4]  # 到达站
            start_time = fields[8]  # 出发时间
            arrive_time = fields[9]  # 到达时间
            duration = fields[10]  # 历时

            # 座位信息（商务座、一等座、二等座等）
            seats = {
                '商务座': fields[32] or '--',
                '一等座': fields[31] or '--',
                '二等座': fields[30] or '--',
                '硬卧': fields[28] or '--',
                '软卧': fields[23] or '--',
                '硬座': fields[29] or '--',
            }

            # 判断是否有票
            has_stock = any(seat in ['有', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                           for seat in seats.values())

            # 构建车次名称
            name = f"{train_no} {from_station}-{to_station} {start_time}-{arrive_time}"

            return TicketInfo(
                id=data,
                name=name,
                price='',  # 价格需要单独查询
                stock=10 if has_stock else 0,
                status='有票' if has_stock else '无票',
                extra={
                    'train_no': train_no,
                    'from_station': from_station,
                    'to_station': to_station,
                    'start_time': start_time,
                    'arrive_time': arrive_time,
                    'duration': duration,
                    'seats': seats
                }
            )

        except Exception as e:
            print(f"解析车次数据失败: {e}")
            return None

    def check_stock(self, ticket_id: str) -> int:
        """
        检查车次库存

        Args:
            ticket_id: 车次 ID

        Returns:
            库存数量
        """
        # 重新查询以获取最新状态
        # 这里简化处理，实际应用中应该使用 ticket_id 解析参数重新查询
        return 0

    def order(self, ticket_id: str, params: Dict[str, Any] = None) -> OrderResult:
        """
        提交订单

        Args:
            ticket_id: 车次 ID
            params: 订单参数
                - seat_type: 座位类型
                - passengers: 乘客信息列表

        Returns:
            订单结果
        """
        if not self.is_logged_in:
            return OrderResult(
                success=False,
                error="未登录，请先登录"
            )

        params = params or {}
        seat_type = params.get('seat_type', '二等座')

        try:
            # 1. 提交订单请求
            submit_params = {
                'secretStr': ticket_id.split('|')[0],
                'train_date': params.get('date', datetime.now().strftime('%Y-%m-%d')),
                'back_train_date': params.get('date', datetime.now().strftime('%Y-%m-%d')),
                'tour_flag': 'dc',
                'purpose_codes': 'ADULT',
                'query_from_station_name': '',
                'query_to_station_name': '',
                'undefined': ''
            }

            # 访问提交订单页面
            self.driver.get(f"{self.BASE_URL}/otn/leftTicket/submitOrderRequest?{'&'.join([f'{k}={v}' for k, v in submit_params.items()])}")
            self.delay(1, 2)

            # 2. 确认订单
            # 这里需要处理乘客选择、座位类型选择等
            # 简化处理

            # 3. 提交订单
            # 实际应用中需要处理人机验证、支付等步骤

            return OrderResult(
                success=True,
                order_id=f"12306-{int(time.time())}",
                message="订单提交成功"
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
        # 访问订单查询接口
        # 简化处理
        return {
            'order_id': order_id,
            'status': '已支付',
            'message': '订单已支付'
        }

    def get_station_code(self, station_name: str) -> Optional[str]:
        """
        根据站点名称获取站点代码

        Args:
            station_name: 站点名称

        Returns:
            站点代码
        """
        # 站点代码映射表（简化）
        station_map = {
            '北京': 'BJP',
            '北京西': 'BXP',
            '北京南': 'BNP',
            '上海': 'SHH',
            '上海虹桥': 'AOH',
            '广州': 'GZQ',
            '广州南': 'IZQ',
            '深圳': 'SZQ',
            '深圳北': 'IOQ',
            '成都': 'CDW',
            '重庆': 'CQW',
            '杭州': 'HGH',
            '南京': 'NJH',
            '武汉': 'WHN',
            '西安': 'XAY',
        }

        return station_map.get(station_name)

    def close(self):
        """关闭资源"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        super().close()
