# -*- coding: utf-8 -*-
from ..manage.env import Application

app = Application()

class ShellExit(SystemExit):
    pass

@app.register
class exit:
    help = None
    usage = """
Usage:
    退出当前shell
            """
    def __init__(self, *args):
        self.args = args or []

        if '--help' in args:
            self.help = True

    def handler(self):
        if self.help:
            print(self.usage)
        else:
            raise ShellExit