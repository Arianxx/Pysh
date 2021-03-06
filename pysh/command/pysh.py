# -*- coding: utf-8 -*-
"""
shell本身也是一个应用，可以通过各种方式访问和控制。初次启动时，直接通过dispatch模块启动shell。

TODO: 将参数判断抽象出来，成为单独的一层，应用只需注册参数类型和列表即可，具体判断交由上层执行。
"""

import os
import sys

from .exit import ShellExit
from ..contrib.LineEdit import LineInput
from ..contrib.parser import Parser
from ..manage.env import Application

app = Application()

@app.register
class pysh:
    line_symbol = '#'
    logout = 'logout'
    slogan = """
    *******************************
    
           Welcome to Pysh!
      Type 'help' to get the help.
       Copyright (c) 2018 ArianX
       
    *******************************
             """
    usage = """
Usage:
    pysh：启动pysh shell
            """

    def __init__(self, *args):
        pass

    def handler(self):
        print(self.slogan)

        self._poll()

        return True

    def _poll(self):
        global input

        if sys.platform == 'win32':
            print('win下行编辑退格时有奇怪的错误，已经关闭行编辑功能')
            print('切换至linux平台体验行编辑(WSL也不行\n')
        else:
            input = LineInput

        while True:
            line_slogan = self.line_symbol + self.curdir + '$'
            try:
                raw_command = input(line_slogan).strip()
            except KeyboardInterrupt:
                print('\n',self.logout)
                break

            if not raw_command:
                continue
            else:
                parser = Parser(raw_command)

            try:
                parser.run()
            except EOFError:
                # 如果是输入流被重定向到文件，文件读尽时会弹出这个错误，代表执行完毕，退出shell
                raise ShellExit
            except ShellExit:
                print(self.logout)
                break

        return True

    @property
    def curdir(self):
        path = os.path.abspath(os.path.curdir)
        path = path.strip('C:').replace("\\", '/')
        return path
