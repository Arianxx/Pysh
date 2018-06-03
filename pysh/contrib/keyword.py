""""
注册特殊符号或关键字。注册时只对tokens做一些必要的清理使之有效，具体的调用逻辑交给parser.Handle,
具体行为交给control.SymbolAction/control.KeywordAction。
"""
import re
from collections import namedtuple, OrderedDict

symbol_mapping = namedtuple('symbol', ['char', 'name', 'cls'])
keyword_mapping = namedtuple('keyword', ['words', 'cls'])

handle_state = namedtuple('state', ['state', 'tokens', 'others'])


class Symbol:
    """
    注册特殊符号
    """
    mapping = OrderedDict()

    @classmethod
    def register(cls, mapping_cls):
        """
        注册特殊符号。

        :param mapping_cls: 遇到特殊符号时将要回调的类。
        :return: 返回原类
        """
        cls.mapping[mapping_cls.name] = symbol_mapping(
            mapping_cls.char,
            mapping_cls.name,
            mapping_cls,
        )

        return mapping_cls


class Keyword:
    """
    注册关键字
    """
    mapping = OrderedDict()

    @classmethod
    def register(cls, mapping_cls):
        """
        注册关键字。

        :param mapping_cls: 映射关键字行为的类。
        :return: 返回原类
        """
        cls.mapping[mapping_cls.words] += keyword_mapping(
            mapping_cls.words,
            mapping_cls,
        )

        return mapping_cls


# 以下是注册的符号类或关键字类


@Symbol.register
class Semicolon:
    """
    执行多条分明的符号
    """
    char = ';'
    name = 'semicolon'

    @classmethod
    def handle(cls, tokens):
        """
        返回经cls.chars分割后的tokens列表。

        :param tokens: 等待分割的tokens
        :return: 分割后的列表
        """
        token_list = []

        def split(tokens):
            nonlocal token_list
            if cls.char in tokens:
                flag = tokens.index(cls.char)
                token_list.append(tokens[0:flag])
                tokens = tokens[flag + 1:]
                split(tokens)
            else:
                if tokens:
                    token_list.append(tokens)
                return

        split(tokens)

        return token_list


@Symbol.register
class daemon:
    """
    末尾有这个符号即启动子进程后台执行。
    """
    char = '&'
    name = 'daemon'

    @classmethod
    def handle(cls, tokens):
        """
        简单的去掉符号并返回，逻辑交给parser中的handler。
        :param tokens:
        :return:
        """
        tokens = tokens[:-1]
        return tokens