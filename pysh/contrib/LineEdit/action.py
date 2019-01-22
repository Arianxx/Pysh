import itertools
import sys

from pysh.command.exit import ShellExit
from pysh.manage.middleware import Completer
from .line_edit import LineInput, KeyMapping, show_history, LineEndError


@LineInput.add_action([KeyMapping.end1, KeyMapping.end2])
def line_end(buffer):
    raise LineEndError()


@LineInput.add_action([KeyMapping.bksp, KeyMapping.clear_prev_char])
def bksp(buffer):
    """
    退格删除
    """
    buffer.pop()


@LineInput.add_action([KeyMapping.completion])
def completion(buffer):
    """
    Tab键命令补全
    """
    if not buffer.content:
        return

    text = ''.join(buffer.content)
    results = []
    for num in itertools.count():
        result = Completer.search_symbol(text, num)
        if not result:
            break
        else:
            results.append(result)

    results = list(set(results))

    if len(results) == 1:
        buffer.clear()
        buffer.content = list(results[0])
    elif not results:
        return False
    else:
        print('\n')
        for result in results:
            print(result, end=' ')
        print('\n')

        print(buffer.slogan, ':', text, sep='', end='')
        sys.stdout.flush()

        return True


@LineInput.add_action([KeyMapping.cursor_to_prev, KeyMapping.left])
def left(buffer):
    """
    左方向键，光标左移。
    """
    if buffer.offset < len(buffer.content):
        buffer.offset += 1


@LineInput.add_action([KeyMapping.cursor_to_next, KeyMapping.right])
def right(buffer):
    """
    右方向键，光标右移
    """
    if buffer.offset > 0:
        buffer.offset -= 1


@LineInput.add_action([KeyMapping.prev_history, KeyMapping.up])
def up(buffer):
    """
    上方向键，上一条历史记录
    """
    show_history(buffer, 1)


@LineInput.add_action([KeyMapping.next_history, KeyMapping.down])
def down(cls, buffer):
    """
    下方向键，下一条历史记录
    """
    show_history(buffer, 0)


@LineInput.add_action([KeyMapping.clear_prev_cursor])
def clear_prev_cursor(buffer):
    """
    清除光标之前的内容
    """
    length = len(buffer.content)
    buffer._prev_remove = buffer.content[:length - buffer.offset]
    buffer.content = buffer.content[length - buffer.offset:]


@LineInput.add_action([KeyMapping.recover_content])
def recover_content(buffer):
    """
    恢复之前清除的内容
    """
    if buffer._prev_remove:
        buffer.content = buffer._prev_remove + buffer.content


@LineInput.add_action([KeyMapping.cursor_to_top])
def cursor_to_top(buffer):
    """
    移动光标到行首
    """
    buffer.offset = len(buffer.content)


@LineInput.add_action([KeyMapping.cursor_to_end])
def cursor_to_end(buffer):
    """
    移动光标到行尾
    """
    buffer.offset = 0


@LineInput.add_action([KeyMapping.clear_prev_word])
def clear_prev_word(buffer):
    """
    清除光标之前的一个单词
    """
    index = len(buffer.content) - buffer.offset - 1
    while index >= 0:
        if buffer.content[index] != ' ' \
                and buffer.content[index] != '\t':
            buffer.content.pop(index)
        else:
            break

        index -= 1


@LineInput.add_action([KeyMapping.clear_cursor_to_end])
def clear_cursor_to_end(buffer):
    """
    清除光标之后的内容
    """
    if buffer.offset:
        buffer.content = buffer.content[:-buffer.offset]


@LineInput.add_action([KeyMapping.swap_two_char])
def swap_two_char(buffer):
    """
    交换光标之前的两个字符
    """
    index = len(buffer.content) - buffer.offset - 1
    buffer.content[index], buffer.content[index - 1] = buffer.content[index - 1], buffer.content[index]


@LineInput.add_action([KeyMapping.exit_shell, KeyMapping.exit_program])
def exit_shell(buffer):
    """
    退出shell
    """
    print('\n')
    raise ShellExit
