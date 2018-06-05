"""
这里定义具体的各个符号和语句的行为，并由parser.Handler.run进行调用
"""
import os
import re
from functools import partial

from .keyword import Symbol, Keyword
from .parser import Parser, Handler
from ..command import pysh, exit
from ..manage.env import Variable, EnvVariable
from ..manage.middleware import StdoutRedirection, StdinRedirection


class SymbolAction:
    """
    注册符号行为的类。
    no_binding_action收集注册的、尚未绑定实例的类。
    """
    no_binding_action = {}

    def __init__(self, handler):
        """
        实例化时绑定parser.Handle的实例，并将自身与收集的行为函数绑定，以便能够像原始方法那样调用。
        """
        self.handler = handler
        self.action = {}
        for name in self.no_binding_action:
            self.action[name] = partial(self.no_binding_action[name], self)

    def __getattr__(self, name):
        """
        使访问注册的方法能够像访问原始方法一样。
        :param name: 注册的方法名
        :return:
        """
        if name in self.action:
            return self.action[name]
        else:
            raise AttributeError(
                "{cls.__name__} object has no attribute {name}".format(cls=type(self), name=name)
            )

    @classmethod
    def register(cls, func):
        name = func.__name__
        cls.no_binding_action.update(
            {
                name: func
            }
        )


class KeywordAction:
    """
    注册关键字行为的类。
    与SymbolAction类似
    """
    no_binding_action = {}

    def __init__(self, handler):
        self.handler = handler
        self.action = {}
        for name in self.no_binding_action:
            self.action[name] = partial(self.no_binding_action[name], self)

    def __getattr__(self, name):
        if name in self.action:
            return self.action[name]
        else:
            raise AttributeError(
                "{cls.__name__} object has no attribute {name}".format(cls=type(self), name=name)
            )

    @classmethod
    def register(cls, func):
        name = func.__name__
        cls.no_binding_action.update(
            {
                name: func
            }
        )


# 以下注册符号行为

@SymbolAction.register
def semicolon(self, tokens):
    """
    分割命令。
    """
    if Symbol.mapping['semicolon'].char in tokens:
        tokens_list = Symbol.mapping['semicolon'].cls.handle(tokens)
        self.handler.tokens = None
        for tokens in tokens_list:
            Handler(tokens).run()

        return


@SymbolAction.register
def backend(self, tokens):
    """
    是否后台执行
    """
    backend = False
    if tokens and tokens[-1] == Symbol.mapping['backend'].char:
        self.handler.tokens = Symbol.mapping['backend'].cls.handle(tokens)
        backend = True

    return backend


@SymbolAction.register
def double_and(self, tokens):
    """
    逻辑与
    """
    if Symbol.mapping['double_and'].char in tokens:
        tokens_list = Symbol.mapping['double_and'].cls.handle(tokens)
        self.handler.tokens = None
        for tokens in tokens_list:
            if Handler(tokens).run():
                continue
            else:
                break
        return


@SymbolAction.register
def dollars(self, tokens):
    """
    当前shell id
    """
    cls = Symbol.mapping['dollars'].cls
    self.handler.tokens = cls.handle(tokens)
    return


@SymbolAction.register
def wave_line(self, tokens):
    """
    用户目录
    """
    cls = Symbol.mapping['wave_line'].cls
    self.handler.tokens = cls.handle(tokens)
    return


@SymbolAction.register
def equal(self, tokens):
    """
    变量赋值
    """
    cls = Symbol.mapping['equal'].cls
    vr_mapping, self.handler.tokens = cls.handle(tokens)
    Variable.variable.update(vr_mapping)
    return


@SymbolAction.register
def dollar(self, tokens):
    """
    变量展开
    """
    cls = Symbol.mapping['dollar'].cls
    self.handler.tokens = cls.handle(tokens)
    return


@SymbolAction.register
def right_angel(self, tokens):
    """
    原来设想的输入输出重定向阶段，应该在分发应用那里，使用装饰器实现来着。
    可是，后来感觉这样解析参数、传来传去的太麻烦，还是就这样吧……
    """
    cls = Symbol.mapping['right_angel'].cls
    if cls.char in tokens:
        file_path, self.handler.tokens = cls.handle(tokens)
        try:
            # 覆盖文件
            sr = StdoutRedirection(file_path, file_override=True)
        except FileNotFoundError as e:
            print(e)
            self.handler.tokens = None
        except PermissionError as e:
            print(e)
            self.handler.tokens = None
        else:
            with sr.context():
                Handler(self.handler.tokens).run()
            self.handler.tokens = None
    return


@SymbolAction.register
def double_right_angel(self, tokens):
    """
    重定向
    """
    cls = Symbol.mapping['double_right_angel'].cls
    if cls.char in tokens:
        file_path, self.handler.tokens = cls.handle(tokens)
        try:
            # 不覆盖文件
            sr = StdoutRedirection(file_path, file_override=False)
        except FileNotFoundError as e:
            print(e)
            self.handler.tokens = None
        except PermissionError as e:
            print(e)
            self.handler.tokens = None
        else:
            with sr.context():
                Handler(self.handler.tokens).run()
            self.handler.tokens = None
    return


@SymbolAction.register
def left_angel(self, tokens):
    """
    重定向输入流
    """
    cls = Symbol.mapping['left_angel'].cls
    if cls.char in tokens:
        file_path, self.handler.tokens = cls.handle(tokens)
        try:
            si = StdinRedirection(file_path=file_path)
        except FileNotFoundError as e:
            print(e)
            self.handler.tokens = None
        except PermissionError as e:
            print(e)
            self.handler.tokens = None
        else:
            try:
                with si.context():
                    Handler(self.handler.tokens).run()
            except UnicodeDecodeError as e:
                # 指定一个非文本文件，读取时会弹出此错误
                print(e)
            self.handler.tokens = None
    return


@SymbolAction.register
def double_left_angel(self, tokens):
    """
    标记式重定向输入流
    """
    cls = Symbol.mapping['double_left_angel'].cls
    if cls.char in tokens:
        tag, tokens = cls.handle(tokens)

        if tag:
            pipe = []
            while True:
                token = input('...').strip()
                if token == tag:
                    break
                else:
                    pipe.append(token)
            si = StdinRedirection(source=pipe)

            try:
                with si.context():
                    Handler(self.handler.tokens).run()
            except TypeError as e:
                print(e)
            finally:
                self.handler.tokens = None
    return


@SymbolAction.register
def back_quote(self, tokens):
    """
    命令替代
    """
    cls = Symbol.mapping['back_quote'].cls
    if cls.char in tokens:
        sub_tokens = cls.handle(tokens)
        if sub_tokens:
            for token in sub_tokens:
                sr = StdoutRedirection()
                with sr.context() as out:
                    Handler(token).run()

                raw_token = ''.join(out.pipe)
                self.handler.raw_token = re.sub('`.*`',
                                                raw_token,
                                                self.handler.raw_token, 1)
            Parser(self.handler.raw_token).run()
            self.handler.tokens = None
    return


# 以下注册关键字行为


@KeywordAction.register
def daemon(self, tokens):
    """
    守护模式
    """
    daemon_map = Keyword.mapping['daemon']
    daemon = False
    if tokens and tokens[-1] == daemon_map.words:
        self.handler.tokens = daemon_map.cls.handle(tokens)
        daemon = True

    return daemon


@KeywordAction.register
def join(self, tokens):
    """
    阻塞模式
    """
    join_map = Keyword.mapping['join']
    join = False
    if join_map.words in tokens:
        self.handler.tokens = join_map.cls.handle(tokens)
        join = True

    return join


@KeywordAction.register
def export(self, tokens):
    """
    设置环境变量
    """
    export_map = Keyword.mapping['export']
    if tokens and export_map.cls.words == tokens[0]:
        vr_dict = export_map.cls.handle(tokens)[0]
        self.handler.tokens = None

        for key, value in vr_dict.items():
            EnvVariable.set_env_variable(key, value)

    return True


@KeywordAction.register
def exec(self, tokens):
    """
    exec命令
    """
    cls = Keyword.mapping['exec']
    if tokens and tokens[0] == cls.words:
        tokens.pop(0)
        if len(tokens) >= 1:
            if tokens[0] == '>':
                tokens.pop(0)
                file_path = tokens[0]
                exec_shell(file_path)
                raise exit.ShellExit
            else:
                Handler(tokens).run()
                self.handler.tokens = None
                raise exit.ShellExit

        self.handler.tokens = tokens
    return


# 辅助函数
def exec_shell(file_path):
    while True:
        path = os.path.abspath(os.path.curdir).strip('C:').replace("\\", '/')
        line_slogan = pysh.pysh.line_symbol + path + '$'
        raw_command = input(line_slogan).strip()

        sr = StdoutRedirection(file_path, False)

        with sr.context():
            if not raw_command:
                continue
            else:
                parser = Parser(raw_command)

            try:
                parser.run()
            except EOFError:
                raise exit.ShellExit
            except exit.ShellExit:
                break

    return True
