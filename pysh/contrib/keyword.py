""""
注册特殊符号或关键字。对tokens做一些与符号本身相关必要的处理（如清洗），具体的调用逻辑交给parser.Handle,
复杂的行为交给control.SymbolAction/control.KeywordAction。

TODO: 类应该按照功能命名而非符号。然而自从开始的几个类名没留意后，惯性的力量是巨大的……
"""
import os
import re
from collections import namedtuple, OrderedDict

from ..manage.env import Processing, Variable, EnvVariable

symbol_mapping = namedtuple('symbol', ['char', 'name', 'derc', 'cls'])
keyword_mapping = namedtuple('keyword', ['words', 'name', 'derc', 'cls'])

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
            mapping_cls.derc,
            mapping_cls,
        )

        return mapping_cls

    @classmethod
    def registered_symbol(cls):
        return OrderedDict(cls.mapping)


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
        cls.mapping[mapping_cls.name] = keyword_mapping(
            mapping_cls.words,
            mapping_cls.name,
            mapping_cls.derc,
            mapping_cls,
        )

        return mapping_cls

    @classmethod
    def registered_keyword(cls):
        return OrderedDict(cls.mapping)


# 以下为符号注册


@Symbol.register
class Semicolon:
    """
    执行多条分明的符号
    """
    char = ';'
    name = 'semicolon'
    derc = '分割多条命令'

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
class Backend:
    """
    末尾有这个符号即启动子进程后台执行。
    """
    char = '&'
    name = 'backend'
    derc = '启动多进程'

    @classmethod
    def handle(cls, tokens):
        """
        简单的去掉符号并返回，逻辑交给parser中的handler。
        :param tokens:
        :return:
        """
        tokens = tokens[:-1]
        return tokens


@Symbol.register
class DoubleAnd:
    """
    逻辑与，只有第一个命令成功返回才执行第二个命令。
    """
    char = '&&'
    name = 'double_and'
    derc = '逻辑与'

    @classmethod
    def handle(cls, tokens):
        """
        像semicolon那样分割列表
        :param tokens:
        :return:
        """
        tokens = [
            token if token != cls.char else Semicolon.char
            for token in tokens
        ]

        return Semicolon.handle(tokens)


@Symbol.register
class Dollars:
    """
    替换为当前shell id.
    """
    char = '$$'
    name = 'dollars'
    derc = '当前shell id'

    @classmethod
    def handle(cls, tokens):
        symbol = cls.char
        shell_id = get_shell_id()
        tokens = list(map(
            lambda token: token.replace(symbol, str(shell_id))
            if cls.char in token
            else token,
            tokens
        ))
        return tokens


@Symbol.register
class WaveLine:
    """
    替换为用户目录。
    """
    char = '~'
    name = 'wave_line'
    derc = '用户目录'
    # win用户目录储存在USERPROFILE环境变量里，linux为HOME
    catalog = os.environ.get('USERPROFILE', None) or os.environ.get('HOME', None)

    @classmethod
    def handle(cls, tokens):
        tokens = list(map(
            lambda token: token if token != cls.char
            else cls.catalog,
            tokens
        ))
        return tokens


@Symbol.register
class Equal:
    """
    设置变量的符号
    """
    char = '='
    name = 'equal'
    derc = '变量赋值'

    @classmethod
    def handle(cls, tokens):
        re_str = r'^[a-zA-Z][a-zA-Z1-9]*=.+$'
        variable_mapping = {}
        for token in list(tokens):
            # 如果都是设置变量的语句，就记录
            if re.match(re_str, token):
                vr_pair = token.split('=')
                variable_mapping.update({vr_pair[0]: vr_pair[1]})
                tokens.pop(tokens.index(token))
            else:
                # 如果后面有其它语句，前面的设置变量的语句就无效
                # 模仿bash的行为
                variable_mapping.clear()
                break
        return (variable_mapping, tokens)


@Symbol.register
class Dollar:
    """
    读取变量
    """
    char = '$'
    name = 'dollar'
    derc = '变量读取声明'

    @classmethod
    def handle(cls, tokens):
        tokens = list(map(
            variable_replace,
            tokens
        ))
        return tokens


@Symbol.register
class BackQuote:
    """
    反引号。用于命令替代
    """
    char = '`'
    name = 'back_quote'
    derc = '命令替代'

    @classmethod
    def handle(cls, tokens):
        sub_tokens = []
        get_sub_tokens(sub_tokens, tokens)
        return sub_tokens


@Symbol.register
class RightAngel:
    """
    重定向输入符号，覆盖文件
    """
    char = '>'
    name = 'right_angel'
    derc = '覆盖式重定向输出'

    @classmethod
    def handle(cls, tokens):
        index = tokens.index(cls.char)
        try:
            tag = tokens[index + 1]
        except IndexError:
            tag = ''
            tokens.pop(index)
        else:
            tokens.pop(index)
            tokens.pop(index)

        return tag, tokens


@Symbol.register
class DoubleRightAngel:
    """
    重定向输出，文件存在不覆盖
    """
    char = '>>'
    name = 'double_right_angel'
    derc = '非覆盖式重定向输出'

    @classmethod
    def handle(cls, tokens):
        index = tokens.index(cls.char)
        try:
            tag = tokens[index + 1]
        except IndexError:
            tag = ''
            tokens.pop(index)
        else:
            tokens.pop(index)
            tokens.pop(index)

        return tag, tokens


@Symbol.register
class LeftAngel:
    """
    将文件内容作为命令输入
    """
    char = '<'
    name = 'left_angel'
    derc = '重定向输入'

    @classmethod
    def handle(cls, tokens):
        index = tokens.index(cls.char)
        try:
            tag = tokens[index + 1]
        except IndexError:
            tag = ''
            tokens.pop(index)
        else:
            tokens.pop(index)
            tokens.pop(index)

        return tag, tokens


@Symbol.register
class DoubleLeftAngel:
    """
    标记式重定向输入。
    将指定标记之间的内容作为输入流。
    """
    char = '<<'
    name = 'double_left_angel'
    derc = '标记式重定向输入'

    @classmethod
    def handle(cls, tokens):
        index = tokens.index(cls.char)
        try:
            tag = tokens[index + 1]
        except IndexError:
            tag = ''
            tokens.pop(index)
        else:
            tokens.pop(index)
            tokens.pop(index)

        return tag, tokens


# 以下为关键字注册

@Keyword.register
class Daemon:
    """
    是否以守护进程方式启动子进程
    """
    words = '--daemon'
    name = 'daemon'
    derc = '进程守护模式'

    @classmethod
    def handle(cls, tokens):
        tokens = tokens[:-1]
        return tokens


@Keyword.register
class Join:
    """
    子进程是否阻塞
    """
    words = '--join'
    name = 'join'
    derc = '进程阻塞'

    @classmethod
    def handle(cls, tokens):
        tokens = list(filter(
            lambda token: True if token != cls.words else False,
            tokens
        ))
        return tokens


@Keyword.register
class Export:
    """
    设置环境变量
    """
    words = 'export'
    name = 'export'
    derc = '设置环境变量'

    @classmethod
    def handle(cls, tokens):
        tokens = tokens[1:]
        return Equal.handle(tokens)


@Keyword.register
class Exec:
    """
    执行单条命令，或整体重定向shell输出
    """
    words = 'exec'
    name = 'exec'
    derc = '执行单条命令/重定向shell输出'

    @classmethod
    def handle(cls, tokens):
        return tokens


# 以下为辅助函数


def get_shell_id():
    """
    得到当前shell id
    """
    processing = Processing.get_records()
    shell_processing = list(filter(
        lambda id: True if processing[id]['NAME'] == 'pysh' else False,
        processing
    ))
    return list(shell_processing)[-1]


def variable_replace(token):
    """
    替换命令里面的变量为值。
    """
    re_str = r'(?P<vr>\$[a-zA-Z][a-zA-Z1-9]*)'
    vr_declares = re.findall(re_str, token)
    for vr_declare in vr_declares:
        vr = Variable.variable.get(vr_declare[1:], False) \
             or EnvVariable.variable.get(vr_declare[1:], '')
        token = token.replace(vr_declare, vr)

    return token


def get_sub_tokens(sub_tokens, tokens):
    """
    递归清洗tokens，得到所有子命令

    :param sub_tokens: 收集子命令的列表
    :param tokens: 原token
    :return: sub_tokens
    """
    sub_token = []
    try:
        bq_1 = tokens.index(BackQuote.char)
    except ValueError:
        return sub_tokens
    else:
        find = False
        for token in tokens[bq_1 + 1:]:
            if token != BackQuote.char:
                sub_token.append(token)
            else:
                find = True
                break
        else:
            sub_token.clear()

        if find:
            # new_tokens = tokens[0:bq_1 + 1]
            # tokens = tokens[bq_1 + 1:]
            tokens.pop(bq_1)
            bq_2 = tokens.index(BackQuote.char)
            # new_tokens += tokens[bq_2:]
            # tokens = new_tokens
            sub_tokens.append(sub_token)
            try:
                get_sub_tokens(sub_tokens, tokens[bq_2 + 1:])
            except IndexError:
                return sub_tokens
        else:
            return sub_tokens
