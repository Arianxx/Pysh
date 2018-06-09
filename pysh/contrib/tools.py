"""
存放一些不适合放在别处的工具性质的类或函数
"""


class _Getch:
    """
    用于行编辑过程。
    读取单个字符。可读取任意字符，包括控制字符。并且兼容win和linux平台。
    参考自stack overflow：
    https://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user/20865751
    """

    def __init__(self):
        self.getch = self._GetchLinux

    def __call__(self):
        self._getch()

        try:
            return self.char.decode()
        except AttributeError:
            return self.char

    def _getch(self):
        self.char = self.getch()

    def _GetchWindows(self):
        import msvcrt
        return msvcrt.getch()

    def _GetchLinux(self):
        try:
            import sys, tty, termios
        except ModuleNotFoundError:
            return self._GetchWindows()
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class LineEndError(ValueError):
    pass


getch = _Getch()
