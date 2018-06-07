"""
实现行编辑的模块。
用这个模块中的函数替换标准的input函数以在想要实现可行编辑的地方使用行编辑。
TODO：实现行编辑
"""

from .tools import getch

class Buffer:
    """
    存放当前输出行的信息
    """
    def __init__(self):
        self.length = 0
        self.pos = 0
        self.content = []

    def flush(self):
        result = ''.join(self.content)
        self.length = 0
        self.pos = 0
        self.content.clear()
        return result

    def clear(self):
        self.length = 0
        self.pos = 0
        self.content.clear()

    def add(self, value):
        self.content.append(value)
        return True

    def pop(self, index=None):
        if index:
            return self.content.pop(index)
        else:
            return self.content.pop(len(self.content) - 1)




