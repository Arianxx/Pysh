# -*- coding: utf-8 -*-
from ..contrib.keyword import Symbol, Keyword
from ..manage.env import Application

app = Application()


@app.register
class help:
    verbose_1 = False
    verbose_2 = False
    verbose_3 = False
    help = False
    usage = """
Usage:
    help(default)：显示本帮助
    help -v：显示注册的命令
    help -vv：显示注册的命令，以及它们各自的用法（如果有）
    help -vvv：显示注册的命令、用法，以及内建的特殊符号和关键字
            """

    def __init__(self, *args):
        self.args = args or []
        if '-v' in self.args:
            self.verbose_1 = True
        elif '-vv' in self.args:
            self.verbose_2 = True
        elif '-vvv' in self.args:
            self.verbose_3 = True
        else:
            self.help = True

    def handler(self):
        if self.help:
            print(self.usage)
        elif self.verbose_1:
            apps = Application.registered_app()
            print('注册的命令有：')
            for app in apps:
                print(app)
        elif self.verbose_2:
            apps = Application.registered_app()
            print('注册的命令有：')
            for name, instance in apps.items():
                print('\n', name)
                try:
                    print('\t', instance.usage)
                except AttributeError:
                    pass
        elif self.verbose_3:
            symbols = Symbol.registered_symbol()
            keywords = Keyword.registered_keyword()
            apps = Application.registered_app()

            print('注册的命令有：')
            for name, instance in apps.items():
                print('\n', name)
                try:
                    print('\t', instance.usage)
                except AttributeError:
                    pass

            print('\n注册的特殊符号有：')
            for key in symbols:
                print(key, ':', symbols[key].char)
                try:
                    print('\tderc: ', symbols[key].derc)
                except AttributeError:
                    pass

            print('\n注册的关键字有：')
            for key in keywords:
                print(key, ':', keywords[key].words)
                try:
                    print('\tderc：', keywords[key].derc)
                except AttributeError:
                    pass

        return True
