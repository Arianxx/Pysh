"""
处理shell一切环境信息，包括记录注册的应用以及从外部环境读取变量等
"""
from datetime import datetime
from collections import deque
from functools import wraps


class Application:
    app = {}

    @staticmethod
    def __new__(cls, *args, **kwargs):
        # Application是一个单例对象。
        if not getattr(cls, '_instance', None):
            cls._instance = super().__new__(cls, *args, **kwargs)

        return cls._instance

    def register(self, cls):
        # 将注册的应用收集到app字典中
        app_name = cls.__name__
        self.app[app_name] = cls

        return cls


class Processing:
    """
    因为没有实现多任务，所以只是记录当前环境中没有退出的命令。例如，在shell里面启动另一个shell（伪），可以通过ps观察到。
    """
    process = {}

    @classmethod
    def record(cls, task):
        """
        记录app实例。

        :param app_instance: 注册自Application.register的app实例
        :return: 成功则返回True
        """
        pid = task.id

        cls.process[pid] = {}
        cls.process[pid]['NAME'] = task._task.__class__.__name__
        cls.process[pid]['TIME'] = datetime.now()
        cls.process[pid]['instance'] = task
        return True

    @classmethod
    def remove(cls, id):
        """
        退出时执行此方法删除记录。

        :param pid: 命令记录在process字典中的pid值。
        :return: 成功与否。
        """
        id = id
        if id in cls.process.keys():
            cls.process.pop(id)
            return True
        return False

    @classmethod
    def get_records(cls):
        """
        每次访问，清理掉无效的记录

        :return: 记录
        """
        for id in list(cls.process):
            if cls.process[id]['instance'].daemon and not cls.process[id]['instance'].is_alive():
                cls.process.pop(id)

        return cls.process


class History:
    """
    记录命令执行的记录。
    """
    history = deque(maxlen=100)

    @classmethod
    def history_recorder(cls, func):
        """
        给dispatch.Dispatch.dispatch函数装饰，记录执行的命令。

        :param func: 待装饰的函数
        :param command: 将执行的命令
        :param args: 命令的参数
        :return: 装饰器
        """

        @wraps(func)
        def decorator(self, command, *args, daemon=False):
            cls.history.append(command)
            return func(self, command, *args, daemon=daemon)

        return decorator

    @classmethod
    def clear(cls):
        """
        清空历史命令
        :return: None
        """

        cls.history.clear()

    @classmethod
    def maxlen(cls):
        return cls.history.maxlen

    @classmethod
    def new_maxlen(cls, value):
        """
        可以修改最大可容纳的历史命令数量。

        :param value: 可以记录的最大命令数
        :return: None
        """
        new_history = deque(maxlen=int(value))
        new_history.extend(cls.history.copy())
        cls.history = new_history


class Variable:
    """
    储存变量
    """
    variable = {}

    @classmethod
    def add(cls, name, value):
        cls.variable[name] = value

    @classmethod
    def remove(cls, name):
        if cls.variable.get(name) is not None:
            cls.variable.pop(name)

    @classmethod
    def clear(cls):
        cls.variable.clear()
