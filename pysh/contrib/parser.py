"""
解析输入的命令。如果命令有特殊符号，执行特殊符号指定的操作。如果命令有控制语句，将解析之后的命令列表交给控制语句。
"""
from shlex import shlex

from ..manage.dispatch import dispatch


class Parser:
    def __init__(self, token):
        """
        对输入的命令做初步分割处理，然后委派给后续类。

        :param token: 输入的命令
        """
        self.token = token

        self.shlex = shlex(self.token, punctuation_chars=True)
        self.shlex.wordchars += '$.\//:'

        self.tokens = list(self.shlex)

    def run(self):
        Handler(self).run()


class Handler:
    """
    对初步分割之后的命令做进一步处理，并执行
    """
    _tokens = None

    def __init__(self, parser):
        try:
            tokens = parser.tokens
            self.raw_token = parser.token
        except AttributeError:
            # 传入Parser的实例对Handler进行初始化是后来为命令替代改变的特性
            # 原来是直接传入分割后的tokens
            # 所以加入try以适应旧的调用方式
            tokens = parser
            self.raw_token = ' '.join(parser)

        tokens = list(filter(lambda token: True if token else False, tokens))
        self.tokens = list(map(lambda token: token.strip(), tokens))

    @property
    def tokens(self):
        return self._tokens

    @tokens.setter
    def tokens(self, tokens):
        """
        tokens是一个特殊属性，在tokens发生改变时，同步修改command和args.

        :param tokens: 变更的tokens
        :return: None
        """
        self.args = None
        self.command = None

        self._tokens = tokens

        if self.tokens:
            self.command = self.tokens[0]
            if len(self.tokens) > 1:
                self.args = self.tokens[1:]

    def _unfold_literal(self):
        """
        展开字面量
        """
        if self.tokens:
            # 展开shell pid
            self.sa.dollars(self.tokens)
            # 展开用户目录
            self.sa.wave_line(self.tokens)
            # 设置变量
            self.sa.equal(self.tokens)
            # 展开变量
            self.sa.dollar(self.tokens)
            # 环境变量
            self.ka.export(self.tokens)

    def _backend(self):
        """
        后台启动相关判断
        """
        # 是否后台启动
        backend = self.sa.backend(self.tokens)
        daemon = False
        join = False
        if backend:
            # 是否守护模式、阻塞
            daemon = self.ka.daemon(self.tokens)
            join = self.ka.join(self.tokens)

        self.backend = backend
        self.daemon = daemon
        self.join = join

    def _redirect(self):
        """
        重定向、替换相关逻辑
        """
        if self.tokens:
            # 重定向输入
            self.sa.left_angel(self.tokens)

        if self.tokens:
            # 标记式重定向输入
            self.sa.double_left_angel(self.tokens)

        if self.tokens:
            # 重定向输出，覆盖文件
            self.sa.right_angel(self.tokens)

        if self.tokens:
            # 重定向输出，不覆盖
            self.sa.double_right_angel(self.tokens)

        if self.tokens:
            # 命令替换
            self.sa.back_quote(self.tokens)

    def _division(self):
        """
        分割语句相关的判断
        """
        if self.tokens:
            # 分号分割语句
            self.sa.semicolon(self.tokens)

        if self.tokens:
            # 逻辑与
            self.sa.double_and(self.tokens)

    def _dispatch(self):
        """
        分发命令
        """
        if self.tokens:
            # 如果没有tokens，说明命令在解析中已经递归执行完毕，直接返回。
            if self.args:
                rv = dispatch.dispatch(self.command, *self.args, backend=self.backend, daemon=self.daemon, join=self.join)
            else:
                rv = dispatch.dispatch(self.command, backend=self.backend, daemon=self.daemon, join=self.join)
        else:
            rv = True

        return rv

    def run(self):
        """
        控制判断符号、关键字的具体逻辑。常在control具体命令中递归执行。

        :return: None
        """
        # 放在这里避免循环导入
        from .control import SymbolAction, KeywordAction
        self.sa = SymbolAction(self)
        self.ka = KeywordAction(self)

        if self.tokens:
            # exec语句
            self.ka.exec(self.tokens)

        self._division()

        self._unfold_literal()

        self._backend()

        self._redirect()

        rv = self._dispatch()

        return rv
