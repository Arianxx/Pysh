"""
处理shell一切环境信息，包括记录注册的应用以及从外部环境读取变量等
"""
import os
from collections import deque
from datetime import datetime
from functools import wraps


class Application:
    app = {}

    @staticmethod
    def __new__(cls, *args, **kwargs):
        # Application是单例。
        if not getattr(cls, '_instance', None):
            cls._instance = super().__new__(cls, *args, **kwargs)

        try:
            import readline
            from .middleware import Completer
        except ImportError:
            # Win下没有readline模块
            pass
        else:
            readline.parse_and_bind("tag: complete")
            readline.set_completer(Completer.search_symbol)

        return cls._instance

    def register(self, cls):
        # 将注册的应用收集到app字典中
        app_name = cls.__name__
        self.app[app_name] = cls

        return cls

    @classmethod
    def registered_app(cls):
        return dict(cls.app)

class Processing:
    """
    记录没有退出的命令的id。
    """
    process = {}

    @classmethod
    def record(cls, task):
        """
        记录命令实例。
        """
        if not cls.process:
            task.id = 0
            pid = task.id
        else:
            index = 0
            while True:
                if index not in cls.process:
                    pid = index
                    break
                index += 1
            task.id = pid

        cls.process[pid] = {}
        cls.process[pid]['NAME'] = task._task.__class__.__name__
        cls.process[pid]['TIME'] = datetime.now()
        cls.process[pid]['instance'] = task
        return True

    @classmethod
    def remove(cls, id):
        """
        退出时执行此方法删除记录。

        :param id: 命令记录在process字典中的pid值。
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
            try:
                if cls.process[id]['instance'].backend and not cls.process[id]['instance'].is_alive():
                    cls.process.pop(id)
            except AssertionError as e:
                # 多个pysh进程下，某些情况会弹出这个错误
                # AssertionError: can only test a child process
                # 经常在exit的时候弹出
                # 并不知道这是什么原因……
                print(e)

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
        :return: 装饰器
        """

        @wraps(func)
        def decorator(self, command, *args, backend=False, daemon=False, join=False):
            cls.history.append(command)
            return func(self, command, *args, backend=backend, daemon=daemon, join=join)

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
    def get_vr(cls, name):
        return cls.variable[name]

    @classmethod
    def remove(cls, name):
        if cls.variable.get(name) is not None:
            cls.variable.pop(name)

    @classmethod
    def clear(cls):
        cls.variable.clear()


class EnvVariable:
    """
    环境变量，以及外部PATH变量
    """
    env_file_path = '/.env'
    variable = {}
    PATH = os.environ['PATH'].split(';')
    cached = {}

    @classmethod
    def set_env_variable(cls, name, value):
        cls.variable.update({name: value})
        with open(cls.env_file_path, 'wt') as file:
            for key, value in cls.variable.items():
                file.write(str(key) + '=' + str(value) + '\n')
        return True

    @classmethod
    def remove_env_variable(cls, name):
        try:
            cls.variable.pop(name)
        except KeyError as e:
            print(e)
        else:
            with open(cls.env_file_path, 'wt') as file:
                for key, value in cls.variable.items():
                    file.write(str(key) + '=' + str(value) + '\n')
        return True

    @classmethod
    def search_path(cls, name):
        if name in cls.cached:
            return cls.cached[name]

        for dir in cls.PATH:
            path = os.path.join(dir, name + '.exe')
            if os.path.isfile(path):
                cls.cached_path(name, path)
                return path
        else:
            return False

    @classmethod
    def cached_path(cls, name, path):
        cls.cached.update({name: path})
        return True

    @classmethod
    def clear_cached(cls):
        cls.cached.clear()
        return True


# 以下辅助函数

def get_env_variable(EnvVariable):
    """
    从文件中读取环境变量。

    :param EnvVariable: EnvVariable类
    :return: 读取的变量名和值的字典
    """
    path = EnvVariable.env_file_path
    try:
        with open(path, 'rt') as file:
            lines = file.readlines()
            variable = {}
            for line in lines:
                try:
                    name, value = line.strip().split('=')
                    name, value = name.strip(), value.strip()
                except Exception:
                    pass
                else:
                    variable.update({name: value})
    except FileNotFoundError as e:
        variable = {}
        pass
    return variable


if not EnvVariable.variable:
    EnvVariable.variable = get_env_variable(EnvVariable)
