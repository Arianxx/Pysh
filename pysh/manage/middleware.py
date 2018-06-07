# -*- coding: utf-8 -*-
import contextlib, sys, os, itertools
from itertools import chain

from ..manage.env import Application, Variable, EnvVariable, History


class StdoutRedirection():
    """
    重定向输出
    """

    def __init__(self, file_path=None, file_override=True):
        """
        如果提供了文件目录，就尝试打开文件，稍后将会将输出重定向到文件。
        否则将输出重定向到内部列表pipe。
        """
        self.file = None
        self.tmp_file = None
        self.pipe = []
        if file_path:
            try:
                if file_override:
                    self.file = open(file_path, 'wt')
                else:
                    self.file = open(file_path, 'at')
            except FileNotFoundError as e:
                """
                只是特别标注出来这里可能弹出的错误。
                错误向上冒泡，具体处理措施交由调用者完成。
                """
                raise e
            except PermissionError as e:
                raise e
        else:
            for num in itertools.count():
                try:
                    self.tmp_file = open('temp'+str(num)+'.txt', 'wt')
                except FileExistsError:
                    continue
                else:
                    break

    @contextlib.contextmanager
    def context(self):
        """
        重定向输出的上下文管理器

        contextlib.contextmanager装饰器自动将协程转换为上下文管理器
        yield前为进入with时执行，yield为with语句返回值，yield后退出with时执行
       """
        origin_stdout = sys.stdout

        if self.file:
            sys.stdout = self.file
        else:
            sys.stdout = self.tmp_file

        try:
            yield self
        except Exception as e:
            raise e
        finally:
            # 不论弹出什么异常，都先还原输出流
            sys.stdout.flush()
            sys.stdout.close()
            sys.stdout = origin_stdout

            with open(self.tmp_file.name, 'rt') as file:
                self.pipe = file.readlines()

            os.remove(self.tmp_file.name)

class StdinRedirection():
    """
    重定向输入
    """
    _source = None

    def __init__(self, file_path=None, source=None):
        """
        如果有文件路径，将输入重定向到文件。否则将输入重定向到source。
        source应该是一个实现了__iter__方法的可迭代对象
        """
        self.file = None
        self.file_path = file_path
        self.source = source

        if self.file_path:
            try:
                file = open(file_path, 'rt')
            except FileNotFoundError as e:
                raise e
            else:
                self.file = file

    def _read(self):
        """
        如果没有传入文件对象，就替换sys.stdin的read和readline替换到实现了read和readline
        方法的实例自身。
        """
        if not self.source:
            raise ValueError("没有输入来源")
        elif not self._source:
            try:
                self._source = iter(self.source)
            except TypeError as e:
                # source没有iter方法
                raise e

    def read(self, *args, **kwargs):
        self._read()

        return '\n'.join(self._source)

    def readline(self, *args, **kwargs):
        self._read()

        return next(self._source)

    @contextlib.contextmanager
    def context(self):
        origin_stdin = sys.stdin

        if self.file:
            sys.stdin = self.file
        else:
            sys.stdin = self

        try:
            yield self
        except StopIteration:
            # _source迭代完毕
            pass
        except Exception as e:
            raise e
        finally:
            # 还原输入流
            if self.file:
                self.file.close()
            sys.stdin = origin_stdin


class Completer:
    @classmethod
    def search_symbol(cls, text, state):
        """
        用于readline模块，以实现linux下的行编辑自动补全功能
        """
        names = [name for name in chain(
            History.history,
            Application.app,
            Variable.variable,
            EnvVariable.variable
        ) if name.startswith(text)]
        try:
            return names[state]
        except IndexError:
            return False
