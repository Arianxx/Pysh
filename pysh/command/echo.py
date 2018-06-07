# -*- coding: utf-8 -*-
from ..manage.env import Application

app = Application()


@app.register
class echo:
    help = False
    usage = """
Usage:
    echo [arg1] [arg2] ...：依次打印参数
    echo --help(default)：打印本帮助
            """

    def __init__(self, *args):
        self.args = args or []
        if not self.args or '--help' in self.args:
            self.help = True

    def handler(self):
        if self.help:
            print(self.usage)
        else:
            for arg in self.args:
                if arg.startswith("'"):
                    arg = arg.strip("'")
                elif arg.startswith('"'):
                    arg = arg.strip('"')

                print(arg, sep=' ')

        return True
