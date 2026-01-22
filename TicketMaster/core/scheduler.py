"""
定时任务调度器模块
基于 APScheduler 实现任务调度功能
"""

from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from models import Task, TaskStatus, TaskType
from core import Database, Logger


class TaskScheduler:
    """任务调度器"""

    def __init__(self, db: Database = None, logger: Logger = None, max_workers: int = 5):
        """
        初始化任务调度器

        Args:
            db: 数据库实例
            logger: 日志实例
            max_workers: 最大工作线程数
        """
        self.db = db
        self.logger = logger
        self.max_workers = max_workers

        # 配置调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=max_workers)
        }
        job_defaults = {
            'coalesce': True,  # 合并延迟的任务
            'max_instances': 1,  # 每个任务最多同时运行一个实例
            'misfire_grace_time': 300  # 错过任务的宽限时间（秒）
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )

        # 任务执行回调函数字典
        self._task_callbacks: Dict[int, Callable] = {}

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("任务调度器已启动")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.logger.info("任务调度器已停止")

    def is_running(self) -> bool:
        """
        检查调度器是否运行中

        Returns:
            是否运行中
        """
        return self.scheduler.running

    def add_task(self, task: Task, callback: Callable):
        """
        添加任务到调度器

        Args:
            task: 任务对象
            callback: 任务执行回调函数
        """
        # 移除旧的任务（如果存在）
        self.remove_task(task.id)

        # 注册回调
        self._task_callbacks[task.id] = callback

        # 创建触发器
        trigger = self._create_trigger(task)

        if trigger:
            # 添加到调度器
            self.scheduler.add_job(
                func=self._execute_task_wrapper,
                trigger=trigger,
                args=[task.id],
                id=str(task.id),
                name=task.name,
                replace_existing=True
            )

            self.logger.info(f"任务已添加到调度器: {task.name} (ID: {task.id})")

    def remove_task(self, task_id: int):
        """
        从调度器移除任务

        Args:
            task_id: 任务 ID
        """
        job_id = str(task_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            self.logger.info(f"任务已从调度器移除: ID {task_id}")

        # 移除回调
        if task_id in self._task_callbacks:
            del self._task_callbacks[task_id]

    def pause_task(self, task_id: int):
        """
        暂停任务

        Args:
            task_id: 任务 ID
        """
        job_id = str(task_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)
            self.logger.info(f"任务已暂停: ID {task_id}")

            # 更新数据库状态
            if self.db:
                self.db.update_task_status(task_id, TaskStatus.PAUSED)

    def resume_task(self, task_id: int):
        """
        恢复任务

        Args:
            task_id: 任务 ID
        """
        job_id = str(task_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)
            self.logger.info(f"任务已恢复: ID {task_id}")

            # 更新数据库状态
            if self.db:
                task = self.db.get_task(task_id)
                if task:
                    self.db.update_task_status(task_id, TaskStatus.PENDING)

    def get_jobs(self) -> List[Dict]:
        """
        获取所有调度中的任务

        Returns:
            任务信息列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs

    def get_job_status(self, task_id: int) -> Optional[str]:
        """
        获取任务的调度状态

        Args:
            task_id: 任务 ID

        Returns:
            状态字符串，如果任务不存在则返回 None
        """
        job_id = str(task_id)
        job = self.scheduler.get_job(job_id)
        if job:
            # 检查任务是否暂停
            if hasattr(job, 'next_run_time') and job.next_run_time is None:
                return 'paused'
            return 'scheduled'
        return None

    def _create_trigger(self, task: Task):
        """
        根据任务类型创建触发器

        Args:
            task: 任务对象

        Returns:
            APScheduler 触发器对象
        """
        if task.task_type == TaskType.ONCE:
            # 一次性任务
            if task.scheduled_time:
                return DateTrigger(run_date=task.scheduled_time)

        elif task.task_type == TaskType.REPEAT_DAILY:
            # 每天执行
            if task.scheduled_time:
                return CronTrigger(
                    hour=task.scheduled_time.hour,
                    minute=task.scheduled_time.minute,
                    second=task.scheduled_time.second
                )

        elif task.task_type == TaskType.REPEAT_WEEKLY:
            # 每周执行
            if task.scheduled_time:
                return CronTrigger(
                    day_of_week=task.scheduled_time.weekday(),
                    hour=task.scheduled_time.hour,
                    minute=task.scheduled_time.minute,
                    second=task.scheduled_time.second
                )

        elif task.task_type == TaskType.REPEAT_MONTHLY:
            # 每月执行
            if task.scheduled_time:
                return CronTrigger(
                    day=task.scheduled_time.day,
                    hour=task.scheduled_time.hour,
                    minute=task.scheduled_time.minute,
                    second=task.scheduled_time.second
                )

        elif task.task_type == TaskType.REPEAT_CUSTOM:
            # 自定义间隔
            if task.repeat_interval:
                return IntervalTrigger(seconds=task.repeat_interval)

        return None

    def _execute_task_wrapper(self, task_id: int):
        """
        任务执行包装器（在调度器中执行）

        Args:
            task_id: 任务 ID
        """
        try:
            # 获取任务
            task = self.db.get_task(task_id) if self.db else None
            if not task:
                self.logger.error(f"任务不存在: ID {task_id}")
                return

            # 更新任务状态为运行中
            if self.db:
                self.db.update_task_status(task_id, TaskStatus.RUNNING)
                task = self.db.get_task(task_id)

            # 调用回调函数
            callback = self._task_callbacks.get(task_id)
            if callback:
                self.logger.info(f"开始执行任务: {task.name} (ID: {task_id})")
                result = callback(task)

                # 更新执行统计
                if self.db:
                    task.executed_count += 1
                    task.last_executed = datetime.now()

                    if result and result.get('success'):
                        task.success_count += 1

                    # 对于一次性任务，执行后更新状态
                    if task.task_type == TaskType.ONCE:
                        if result and result.get('success'):
                            self.db.update_task_status(task_id, TaskStatus.SUCCESS)
                        else:
                            self.db.update_task_status(
                                task_id,
                                TaskStatus.FAILED,
                                error_message=result.get('error', '') if result else ''
                            )

                    self.db.update_task(task)

            else:
                self.logger.error(f"任务没有回调函数: ID {task_id}")

        except Exception as e:
            self.logger.exception(f"执行任务时发生异常: ID {task_id}")
            if self.db:
                self.db.update_task_status(task_id, TaskStatus.FAILED, str(e))

    def load_tasks_from_db(self, callback: Callable):
        """
        从数据库加载所有待执行的任务

        Args:
            callback: 任务执行回调函数
        """
        if not self.db:
            return

        # 获取所有待执行的任务
        tasks = self.db.get_tasks_by_status(TaskStatus.PENDING)

        for task in tasks:
            # 检查任务是否过期
            if task.scheduled_time and task.scheduled_time < datetime.now():
                if task.task_type == TaskType.ONCE:
                    # 一次性任务过期，标记为失败
                    self.db.update_task_status(task.id, TaskStatus.FAILED, "任务已过期")
                    continue

            # 添加到调度器
            self.add_task(task, callback)

        self.logger.info(f"从数据库加载了 {len(tasks)} 个任务")

    def reschedule_task(self, task: Task, callback: Callable):
        """
        重新调度任务

        Args:
            task: 任务对象
            callback: 任务执行回调函数
        """
        self.remove_task(task.id)
        self.add_task(task, callback)

    def get_next_run_time(self, task_id: int) -> Optional[datetime]:
        """
        获取任务的下次执行时间

        Args:
            task_id: 任务 ID

        Returns:
            下次执行时间，如果任务不存在则返回 None
        """
        job_id = str(task_id)
        job = self.scheduler.get_job(job_id)
        return job.next_run_time if job else None
