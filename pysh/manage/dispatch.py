"""
Dispatch接受解析之后的参数，将参数分发给应用执行，并执行环境需要的其它操作。
"""
import os
import subprocess
import sys
from multiprocessing import Process

from .env import Application, Processing, History, Variable, EnvVariable
from .middleware import StdinRedirection

apps = Application.app


class Task(Process):
    """
    包装真正的命令。
    """

    def __init__(self, app, *args):
        super().__init__()
        self.app = app
        self.args = args
        self.name = self.app.__class__.__name__
        self.backend = False
        self.is_join = False

        if type(self.app) != str:
            # 不是字符串说明是内部注册的命令类
            self._task = self.app(*self.args)

            # 绑定当前环境到应用，以便多进程下能够访问
            self._task.env = {
                'app': Application.app,
                'process': Processing.process,
                'history': History.history,
                'variable': Variable.variable,
            }
        else:
            # 否则是外部命令路径
            self._task = None

    def run(self):
        if self.backend:
            # 如果是后台程序，强制打开输入流
            sys.stdin = os.fdopen(0)

            if self._task:
                Application.app = self._task.env['app']
                Processing.process = self._task.env['process']
                History.history = self._task.env['history']

        if self._task:
            self._task.env.update(
                Application=Application,
                Processing=Processing,
                History=History,
                Variable=Variable,
            )

        Processing.record(self)

        try:
            if self._task:
                # 内部命令，调用注册的方法
                rv = self._task.handler()
            else:
                # 外部命令打开子进程
                rv = subprocess.call([self.app] + [*self.args])
        except EOFError as e:
            # 子进程可能会发生io错误
            print(e)
            rv = False
        except Exception as e:
            # 其它异常向上冒泡
            raise e
        finally:
            # 清理记录
            Processing.remove(self.id)

        return rv


class Script:
    """
    如果传入一个文件路径，尝试使用shebang或内置的命令解析这个文件
    """

    def __init__(self, path):
        self.path = path.strip()

    def _read(self):
        """
        尝试读取文件
        """
        try:
            file = open(self.path, 'rt')
        except FileNotFoundError as e:
            print(e)
            raise e
        except PermissionError as e:
            print(e)
            raise e

        self.file = file

        try:
            self.lines = self.file.readlines()
        except UnicodeDecodeError as e:
            print(e)
            raise e
        finally:
            self.file.close()

        return

    def _dispatch(self):
        """
        如果有shebang则用shebang对应的程序运行。
        否则自身运行
        """
        if not self.lines:
            raise ValueError("没有输入")

        shebang = None
        for line in self.lines:
            if line.startswith('#'):
                if line.startswith('#!'):
                    shebang = line.strip('#!').strip()
                else:
                    continue
            else:
                break

        if shebang:
            try:
                subprocess.call([shebang, self.path])
                return True
            except FileNotFoundError as e:
                print(e)
                return False
        else:
            return self._parse()

    def _parse(self):
        """
        重定向输入到文件,一行一行解析
        """
        from ..contrib.parser import Parser

        tokens = self.lines[1:]
        si = StdinRedirection(source=tokens)
        rv = True
        with si.context():
            while True:
                # 虽然是while True，tokens读尽时，上下文管理器弹出StopIteration，捕获后会退出循环
                token = input()
                try:
                    Parser(token).run()
                except Exception as e:
                    print(e)
                    rv = False
                    break
        return rv

    def run(self):
        try:
            self._read()
        except Exception as e:
            print(e)
            return False

        return self._dispatch()


class Dispatch:
    def __init__(self):
        pass

    def _thread(self, app, *args, daemon=False, join=False):
        """
        后台命令就新建一个进程。

        :param app: 要启动的app类
        :param args: 命令的参数
        :return: None
        """
        task = Task(app, *args)
        task.backend = True
        if join:
            task.is_join = True

        # 守护进程
        # 如果进程以守护进程的方式启动，在父进程结束时，守护进程也立即结束。
        # 并且，以守护进程方式启动，会导致输入混乱。如果以守护进程启动新pysh
        # 会导致两个shell交替相应输入
        task.daemon = daemon

        try:
            task.start()
        except AssertionError as e:
            # 父进程以守护模式启动，就不能再创建子进程。
            # 会弹出:
            # AssertionError: daemonic processes are not allowed to have children
            # 虽然我并不明白为什么不能创建
            # 总之先忽略它吧……
            print(e)

        # 子进程是否阻塞
        # 在pysh中启动一个新pysh，应该使其阻塞，否则会产生混乱
        if join:
            task.join()

        # 启动子进程后在父进程也记录子进程的id
        Processing.record(task)
        return True

    def _front(self, app, *args):
        """
        前台程序直接手动启动。

        :param app: 要启动的app类
        :param args: 命令的参数
        :return: None
        """
        task = Task(app, *args)
        return task.run()

    def _script(self, file_path):
        """
        尝试解析脚本
        """
        return Script(file_path).run()

    @History.history_recorder
    def dispatch(self, command, *args, backend, daemon, join):
        # 先搜索注册的应用，没有就搜寻环境PATH变量
        app = apps.get(command, None) or EnvVariable.search_path(command)

        if app:
            if backend:
                # rv = return_value
                rv = self._thread(app, *args, daemon=daemon, join=join)
            else:
                rv = self._front(app, *args)
        elif os.path.isfile(command):
            # 如果是文件路径，尝试按照shebang运行或自身解析
            rv = self._script(command)
        else:
            print('{}: command not found'.format(command))
            rv = False

        return rv


dispatch = Dispatch()
