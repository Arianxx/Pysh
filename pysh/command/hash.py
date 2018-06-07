# -*- coding: utf-8 -*-
from ..manage.env import Application, EnvVariable

app = Application()


@app.register
class hash:
    clear = False
    show = False
    help = False
    usage = """
Usage:
    hash -l：查看缓存的路径
    hash -r: 清空缓存的外部命令路径
    hash --help(default)：显示本帮助
            """

    def __init__(self, *args):
        self.args = args or []
        if not self.args or '--help' in self.args or not self.args:
            self.help = True
        elif '-l' in self.args:
            self.show = True
        elif '-r' in self.args:
            self.clear = True

    def handler(self):
        rv = True

        if self.help:
            print(self.usage)
        elif self.show:
            for name, path in EnvVariable.cached.items():
                print(name + ' : ' + path)
        elif self.clear:
            length = len(EnvVariable.cached)
            if not EnvVariable.clear_cached():
                rv = False
            else:
                print('已经清空 {} 外部命令路径'.format(length))

        return rv
