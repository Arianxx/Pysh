"""
shell本身也是一个应用，可以通过各种方式访问和控制。初次启动时，直接通过dispatch模块启动shell。
"""

import os
from .exit import ShellExit
from ..manage.env import Application, Processing
from ..contrib.parser import Parser

app = Application()


@app.register
class pysh:
    line_symbol = '#'
    logout = 'logout'
    slogan = """
    *******************************
    
           Welcome to Pysh!
       Copyright (c) 2018 ArianX
       
    *******************************
             """

    def __init__(self, *args):
        pass

    def handler(self):
        print(self.slogan)

        while True:
            line_slogan = self.line_symbol + self.curdir + '$'
            raw_command = input(line_slogan).strip()

            if not raw_command:
                continue
            else:
                parser = Parser(raw_command)

            try:
                parser.run()
            except ShellExit as e:
                print(self.logout)
                break

    @property
    def curdir(self):
        path = os.path.abspath(os.path.curdir)
        path = path.strip('C:').replace("\\", '/')
        return path
