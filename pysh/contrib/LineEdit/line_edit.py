"""
实现行编辑的模块。
用这个模块中的LineInput类替换标准的input函数以在想要实现可行编辑的地方使用行编辑。
"""
import re
import sys
from collections import defaultdict

from pysh.contrib.tools import getch, LineEndError
from pysh.manage.env import History


class Buffer:
    """
    存放当前编辑行的信息
    """

    def __init__(self):
        # 光标位置。离末尾字符的偏移量
        self.offset = 0
        # 已经打印出来，显示在屏幕上的字符
        self.showed = 0
        # 已经打印出的光标的偏移量
        self.offseted = 0
        # 组合键缓冲区
        self._group_key = ''
        # 处于历史记录的位置
        self._history_index = -1
        # 前一次ctrl + U删除的内容
        self._prev_remove = []
        # 缓冲区的字符
        self.content = []

    def _group_key_buffer(self, key):
        """
        部分键比较特殊，是字符组合形式。比如按一下方向键产生三个字符
        所以为了识别这类键建立一个特殊的方法。
        """
        if key == KeyMapping.esc:
            self._group_key = KeyMapping.esc
            return False
        elif self._group_key.startswith(KeyMapping.esc):
            self._group_key += key

        if self._group_key == KeyMapping.left:
            self.pop()
            self._group_key = ''
            return KeyMapping.left
        elif self._group_key == KeyMapping.right:
            self.pop()
            self._group_key = ''
            return KeyMapping.right
        elif self._group_key == KeyMapping.up:
            self.pop()
            self._group_key = ''
            return KeyMapping.up
        elif self._group_key == KeyMapping.down:
            self.pop()
            self._group_key = ''
            return KeyMapping.down
        elif self._group_key == KeyMapping.home:
            self.pop()
            self.pop()
            self._group_key = ''
            return KeyMapping.home
        elif self._group_key == KeyMapping.end:
            self.pop()
            self.pop()
            self._group_key = ''
            return KeyMapping.end

        if len(self._group_key) >= 4:
            self._group_key = ''

        return False

    def flush(self):
        result = ''.join(self.content)
        self.offset = 0
        self.content.clear()
        return result

    def clear(self):
        self.pos = 0
        self.offset = 0
        self.content.clear()

    def add(self, value):
        self.content.append(value)
        return True

    def pop(self):
        index = len(self.content) - self.offset - 1
        if index >= 0:
            return self.content.pop(index)
        else:
            pass

    def insert(self, value, offset=None):
        if not offset:
            self.content.append(value)
        else:
            self.content.insert(len(self.content) - offset, value)

    def show(self):
        print(' ' * self.offseted, sep='', end='')
        print('\x08' * self.showed, ' ' * self.showed, '\x08' * self.showed, sep='', end='')
        content = ''.join(self.content)
        print(content, sep='', end='')
        print('\x08' * self.offset, sep='', end='')
        self.showed = len(content)
        self.offseted = self.offset
        sys.stdout.flush()


class KeyMapping:
    end1 = '\n'
    end2 = '\r'
    bksp = '\x08'  # 退格
    completion = '\t'  # tab
    esc = '\x1b'
    left = '\x1b[D'
    right = '\x1b[C'
    up = '\x1b[A'
    down = '\x1b[B'
    clear_prev_cursor = '\x15'  # ctrl + u
    clear_prev_char = '\x08'  # ctrl + h
    exit_shell = '\x04'  # ctrl + d
    exit_program = '\x03'  # ctrl + c
    prev_history = '\x10'  # ctrl + p
    next_history = '\x0e'  # ctrl + n
    recover_content = '\x19'  # ctrl + y
    cursor_to_top = '\x01'  # ctrl + a
    cursor_to_end = '\x05'  # ctrl + e
    clear_prev_word = '\x17'  # ctrl + w
    clear_cursor_to_end = '\x0b'  # ctrl + k
    swap_two_char = '\x14'  # ctrl + t
    cursor_to_next = '\x06'  # ctrl + f
    cursor_to_prev = '\x02'  # ctrl + b
    home = '\x1b[1~'  # home键
    end = '\x1b[4~'  # end键

    direct_prev_history = '!!'
    prev_n_history = r'^!-(?P<num>\d+)$'
    echo_prev_history = r'^!-(?P<num>\d+):p$'
    last_like_history = r'^!\?(?P<text>[a-zA-Z0-9]+)\?$'

    @classmethod
    def _get_map_dict(cls):
        return {name: getattr(cls, name) for name in dir(cls) \
                if not name.startswith('_')}


class LineInput:
    dispatcher = defaultdict(list)

    @staticmethod
    def __new__(cls, slogan):
        buffer = Buffer()
        buffer.slogan = slogan

        buffer.clear()

        print(slogan, ':', sep='', end='')
        sys.stdout.flush()

        while True:
            char = getch().strip('\x00')
            try:
                if not len(char) == 1:
                    for ch in char:
                        cls._handler(ch, buffer)
                else:
                    cls._handler(char, buffer)
            except LineEndError:
                print('\n')
                break

        text = cls._command_handler(buffer.flush(), buffer)
        return text

    @classmethod
    def add_action(cls, symbols=(None)):
        def decorator(func):
            for symbol in symbols:
                cls.dispatcher[symbol].append(func)
            return func

        return decorator

    @classmethod
    def _handler(cls, char, buffer):
        is_group = buffer._group_key_buffer(char)

        if is_group:
            char = is_group
        elif ord(char) in range(32, 127):
            buffer.insert(char, buffer.offset)
        elif char not in cls.dispatcher:
            char = None

        if char in cls.dispatcher:
            for func in cls.dispatcher[char]:
                func(buffer)

        buffer.show()

    @classmethod
    def _command_handler(cls, text, buffer):
        if text == KeyMapping.direct_prev_history:
            return cls.direct_prev_history(buffer)

        num = re.findall(KeyMapping.prev_n_history, text)
        if num:
            num = num[0]
            return cls.prev_n_history(num)

        num = re.findall(KeyMapping.echo_prev_history, text)
        if num:
            num = num[0]
            return cls.echo_prev_history(num)

        like_text = re.findall(KeyMapping.last_like_history, text)
        if like_text:
            like_text = like_text[0]
            return cls.last_like_history(like_text)

        return text

    @classmethod
    def _get_history(cls, buffer, arrow):
        """
        得到指定的历史记录。
        arrow为 1 代表下一条历史记录，为 0 代表上一条历史记录
        """
        length = len(History.history) - 1
        arrow = 'prev' if arrow else 'next'
        if arrow == 'prev':
            if buffer._history_index < length:
                buffer._history_index += 1
                return History.history[length - buffer._history_index]
            else:
                return History.history[length]
        elif arrow == 'next':
            if buffer._history_index > 1:
                buffer._history_index -= 1
                return History.history[length - buffer._history_index]
            else:
                return History.history[0]

    @classmethod
    def direct_prev_history(cls, buffer):
        """
        直接执行上一条历史记录
        """
        return cls._get_history(buffer, 1)

    @classmethod
    def prev_n_history(cls, n):
        """
        执行上第n条历史记录
        """
        index = len(History.history) - int(n)
        return History.history[index]

    @classmethod
    def echo_prev_history(cls, n):
        """
        打印上第n条历史记录不执行
        """
        index = len(History.history) - int(n)
        print(History.history[index])
        return ''

    @classmethod
    def last_like_history(cls, text):
        """
        执行最近一条包含text的历史记录
        """
        index = len(History.history) - 1
        while index >= 0:
            if text in History.history[index]:
                print(History.history[index])
                return History.history[index]

            index -= 1

        return ''


def show_history(buffer, arrow):
    """
    展示历史记录，arrow代表方向
    """
    history = LineInput._get_history(buffer, arrow)

    buffer.content = list(history)
    buffer.offseted = buffer.offset = 0
    return True
