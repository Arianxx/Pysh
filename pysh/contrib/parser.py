"""
解析输入的命令。如果命令有特殊符号，执行特殊符号指定的操作。如果命令有控制语句，将解析之后的命令列表交给控制语句。
"""
from shlex import shlex
from ..manage.dispatch import dispatch

class Parser:
    def __init__(self, token):
        """
        对输入的命令做简单的分割处理，然后委派给后续类。

        :param token: 输入的命令
        """
        self.token = token

        self.shlex = shlex(self.token, punctuation_chars=True)
        self.shlex.wordchars += '$'

        self.tokens = list(self.shlex)

    def run(self):
        Handler(self.tokens).run()


class Handler:
    """
    对出解析之后的命令做进一步处理、执行
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.command = self.tokens[0]

        if len(self.tokens) > 1:
            self.args = self.tokens[1:]
        else:
            self.args = None

    def run(self):
        """
        控制判断符号、关键字的具体逻辑

        :return: None
        """
        # 放在这里避免循环导入
        from .control import SymbolAction
        sa = SymbolAction(self)

        sa.semicolon(self.tokens)

        daemon = sa.daemon(self.args)

        if self.args:
            dispatch.dispatch(self.command, *self.args, daemon=daemon)
        else:
            dispatch.dispatch(self.command, daemon=daemon)