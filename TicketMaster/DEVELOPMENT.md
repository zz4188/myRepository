# TicketMaster 开发文档

## 📁 项目结构

```
TicketMaster/
├── main.py                      # 程序入口
├── requirements.txt             # 依赖清单
├── setup.py                     # 安装脚本
├── build_exe.py                 # 打包脚本
├── TicketMaster.spec            # PyInstaller 配置
├── install.bat                  # Windows 安装脚本
├── run.bat                      # Windows 运行脚本
├── installer.nsi                # NSIS 安装程序脚本
├── version_info.txt             # 版本信息
├── README.md                    # 使用文档
├── QUICKSTART.md                # 快速入门
├── LICENSE                      # 许可证
├── .gitignore                   # Git 忽略文件
│
├── gui/                         # GUI 模块
│   ├── __init__.py
│   ├── main_window.py           # 主窗口（菜单、工具栏、状态栏、标签页）
│   ├── accounts_widget.py       # 账号管理界面
│   ├── tasks_widget.py          # 任务管理界面
│   ├── logs_widget.py           # 日志查看界面
│   └── settings_widget.py       # 设置界面
│
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── database.py              # SQLite 数据库层
│   ├── logger.py                # 日志系统
│   └── scheduler.py             # APScheduler 定时任务调度器
│
├── platforms/                   # 平台模块
│   ├── __init__.py
│   ├── base_platform.py         # 平台基类（定义通用接口）
│   ├── platform_12306.py        # 12306 平台实现
│   ├── platform_damai.py        # 大麦网平台实现
│   └── platform_ctrip.py        # 携程平台实现
│
├── utils/                       # 工具模块
│   ├── __init__.py
│   ├── encryption.py           # 密码加密（cryptography）
│   ├── proxy.py                 # 代理管理（HTTP/SOCKS5）
│   └── config.py                # 配置管理（JSON）
│
├── models/                      # 数据模型
│   ├── __init__.py
│   ├── account.py               # 账号模型
│   └── task.py                  # 任务模型
│
└── icons/                       # 图标资源
    ├── README.md                # 图标说明
    └── placeholder.txt         # 占位说明
```

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────────────────┐
│          Presentation Layer             │
│          (PyQt6 GUI)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Accounts │ │  Tasks   │ │  Logs    │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────┘
                    ▲
                    │ Signals/Slots
                    ▼
┌─────────────────────────────────────────┐
│          Business Logic Layer           │
│          (任务调度、抢票逻辑)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Scheduler │ │  Logger  │ │ Platform │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────┘
                    ▲
                    │
                    ▼
┌─────────────────────────────────────────┐
│            Data Access Layer             │
│          (SQLite Database)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Accounts │ │  Tasks   │ │  Logs    │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────┘
```

### 核心组件说明

#### 1. 数据库层 (core/database.py)
- 职责：数据持久化、CRUD 操作
- 技术：SQLite
- 功能：
  - 账号管理（增删改查）
  - 任务管理（状态更新）
  - 日志记录（持久化）
  - 索引优化

#### 2. 日志系统 (core/logger.py)
- 职责：统一日志记录
- 技术：logging + colorlog
- 功能：
  - 多级别日志（DEBUG, INFO, WARNING, ERROR, SUCCESS, CRITICAL）
  - 控制台输出（彩色）
  - 文件输出（按日期分割）
  - 数据库存储

#### 3. 任务调度器 (core/scheduler.py)
- 职责：任务调度和执行
- 技术：APScheduler
- 功能：
  - 一次性任务
  - 周期性任务（日、周、月、自定义）
  - 任务队列管理
  - 并发控制
  - 错误重试

#### 4. 平台模块 (platforms/)
- 职责：实现各平台的抢票逻辑
- 技术：Selenium + requests
- 功能：
  - 统一的接口（BasePlatform）
  - 登录认证
  - 票务查询
  - 自动下单
  - 反爬虫机制

#### 5. GUI 模块 (gui/)
- 职责：用户界面
- 技术：PyQt6
- 功能：
  - 主窗口框架
  - 账号管理界面
  - 任务管理界面
  - 日志查看界面
  - 设置界面

#### 6. 工具模块 (utils/)
- 职责：通用工具函数
- 技术：cryptography, requests
- 功能：
  - 密码加密/解密
  - 代理管理
  - 配置管理

## 🔄 数据流程

### 登录流程

```
用户输入账号密码
    ↓
GUI: AccountsWidget
    ↓
加密存储（encryption.py）
    ↓
保存到数据库（database.py）
    ↓
测试连接
    ↓
调用平台登录（platform_*.py）
    ↓
保存 cookies
    ↓
更新账号状态
```

### 抢票流程

```
创建任务
    ↓
保存到数据库
    ↓
添加到调度器（scheduler.py）
    ↓
等待执行时间
    ↓
执行任务回调
    ↓
1. 获取账号
    ↓
2. 平台登录
    ↓
3. 搜索票务
    ↓
4. 检查库存
    ↓
5. 提交订单
    ↓
6. 返回结果
    ↓
更新任务状态
    ↓
记录日志
```

## 🔧 技术要点

### 1. 密码安全
- 使用 Fernet 对称加密（cryptography）
- 密钥派生（PBKDF2HMAC）
- 不在内存中存储明文密码
- 数据库只存储加密后的密码

### 2. 反爬虫机制
- 随机请求延迟
- 随机 User-Agent
- 代理轮换
- 请求头伪装
- Cookie 管理
- 浏览器自动化（Selenium）

### 3. 多线程安全
- GUI 运行在主线程
- 抢票任务在后台线程
- 使用 PyQt Signal/Slot 通信
- 线程安全的数据访问

### 4. 异常处理
- 完善的异常捕获
- 友好的错误提示
- 自动重试机制
- 日志记录详细错误信息

## 📊 数据库设计

### accounts 表
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,           -- 平台类型
    username TEXT NOT NULL,            -- 用户名
    password TEXT NOT NULL,            -- 加密后的密码
    status TEXT NOT NULL,              -- 状态
    nickname TEXT,                     -- 昵称
    phone TEXT,                        -- 手机号
    email TEXT,                        -- 邮箱
    cookies TEXT,                      -- 登录 cookies
    last_login DATETIME,               -- 最后登录时间
    created_at DATETIME,               -- 创建时间
    updated_at DATETIME,               -- 更新时间
    remark TEXT                        -- 备注
);
```

### tasks 表
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                -- 任务名称
    platform TEXT NOT NULL,            -- 平台类型
    status TEXT NOT NULL,              -- 状态
    task_type TEXT NOT NULL,           -- 任务类型
    scheduled_time DATETIME,            -- 计划执行时间
    repeat_interval INTEGER,            -- 重复间隔
    account_ids TEXT,                  -- 账号ID列表（JSON）
    params TEXT,                       -- 任务参数（JSON）
    executed_count INTEGER,             -- 已执行次数
    success_count INTEGER,             -- 成功次数
    last_executed DATETIME,             -- 最后执行时间
    next_execute DATETIME,              -- 下次执行时间
    error_message TEXT,                -- 错误信息
    created_at DATETIME,               -- 创建时间
    updated_at DATETIME,               -- 更新时间
    remark TEXT                        -- 备注
);
```

### logs 表
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,               -- 日志级别
    message TEXT NOT NULL,              -- 日志消息
    task_id INTEGER,                   -- 关联任务ID
    account_id INTEGER,                -- 关联账号ID
    platform TEXT,                     -- 平台类型
    created_at DATETIME,               -- 创建时间
    extra_data TEXT                    -- 额外数据（JSON）
);
```

## 🎨 UI 设计

### 颜色方案
- 主色调：蓝色 (#007bff)
- 成功：绿色
- 警告：黄色
- 错误：红色
- 信息：蓝色
- 背景：浅灰色 (#f5f5f5)

### 界面布局
- 顶部：菜单栏
- 菜单栏下方：工具栏
- 中央：标签页（TabWidget）
- 底部：状态栏
- 系统托盘：最小化图标

### 交互设计
- 双击行进行编辑
- 右键菜单快捷操作
- 实时刷新状态
- 友好的确认对话框
- 详细的错误提示

## 🚀 扩展开发

### 添加新平台

1. 继承 `BasePlatform` 类
2. 实现必需的方法：
   - `get_platform_name()`
   - `get_platform_code()`
   - `login(account)`
   - `search(params)`
   - `check_stock(ticket_id)`
   - `order(ticket_id, params)`
   - `get_order_status(order_id)`
3. 在 `main_window.py` 中注册

### 添加新功能

1. 确定功能模块（GUI 或 Core）
2. 设计数据模型（如需要）
3. 实现 UI 界面（如需要）
4. 实现业务逻辑
5. 更新数据库 schema（如需要）
6. 添加日志记录

## 📝 代码规范

### 命名约定
- 类名：大驼峰（PascalCase）
- 函数名：小写下划线（snake_case）
- 变量名：小写下划线（snake_case）
- 常量名：大写下划线（UPPER_SNAKE_CASE）
- 私有成员：前缀下划线（_private）

### 文档字符串
- 所有类和公共方法必须有文档字符串
- 使用 Google 风格或 NumPy 风格
- 包含参数说明和返回值说明

### 注释
- 复杂逻辑添加注释说明
- 关键步骤添加注释
- 保持注释简洁明了

## 🐛 调试技巧

### 1. 启用调试日志
在设置中将日志级别设置为 DEBUG

### 2. 查看实时日志
使用"日志查看"标签页实时查看日志

### 3. 测试单个功能
在 Python 交互环境中导入模块测试

### 4. 捕获异常
使用 try-except 捕获异常并记录详细错误信息

## 📚 参考资料

### Python
- [Python 官方文档](https://docs.python.org/zh-cn/3/)
- [PyQt6 官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt6/)

### 框架和库
- [Selenium 文档](https://www.selenium.dev/documentation/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [requests 文档](https://requests.readthedocs.io/)
- [cryptography 文档](https://cryptography.io/)

### 打包工具
- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [NSIS 文档](https://nsis.sourceforge.io/Docs/)

---

## 💡 最佳实践

1. **错误处理**
   - 始终捕获和处理异常
   - 提供友好的错误提示
   - 记录详细的错误日志

2. **性能优化**
   - 避免阻塞 GUI 线程
   - 使用连接池管理数据库
   - 合理设置请求延迟

3. **安全考虑**
   - 敏感信息加密存储
   - 不在日志中记录密码
   - 定期清理日志和数据

4. **代码质量**
   - 遵循 PEP 8 规范
   - 编写单元测试
   - 定期代码审查

5. **用户体验**
   - 提供进度反馈
   - 支持取消操作
   - 友好的错误提示
