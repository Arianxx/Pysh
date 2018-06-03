"""
这里定义具体的各个符号和语句的行为，并由parser.Handler.run进行调用
"""

from .keyword import Symbol, Keyword
from .parser import Handler

class SymbolAction:
    def __init__(self, handler):
        self.handler = handler

    def semicolon(self, tokens):
        if Symbol.mapping['semicolon'][0] in tokens:
            tokens_list = Symbol.mapping['semicolon'][2].handle(tokens)
            for tokens in tokens_list:
                Handler(tokens).run()
            return

    def daemon(self, args):
        daemon = False
        if args:
            if args[-1] == Symbol.mapping['daemon'][0]:
                self.handler.args = Symbol.mapping['daemon'][2].handle(args)
                daemon = True

        return daemon