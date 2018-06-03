import os
from ..manage.env import Application

app = Application()

@app.register
class cd:
    help = None
    path = None
    usage = """
Usage:
    cd path：改变当前工作目录为 path
    cd --help：显示这个帮助信息
            """
    def __init__(self, *args):
        if '--help' in args:
            self.help = True
        else:
            self.path = args[0]

    def handler(self):
        if self.path:
            try:
                os.chdir(self.path)
            except FileNotFoundError as e:
                print(e)
            except NotADirectoryError as e:
                print(e)
        elif self.help:
            print(self.usage)

        return
