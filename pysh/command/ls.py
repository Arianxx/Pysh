import os
from ..manage.env import Application

app = Application()


@app.register
class ls:
    almost_all = True
    all = None
    ignore_back_backups = None
    list = None
    reverse = None
    help = None
    paths = None
    usage = """
Usage:
    ls [optional] [path1] [path2] ...
Optional:
    ls -A, -almost-all: 列出除了 . 和 .. 的所有文件
    ls -a, -all: 列出目录下的所有文件，包括以. 开头的隐含文件
    ls -B, -ignore-back-backups：不列出任何以 ~ 字符结束的文件
    ls -l, -list：列排列输出
    ls -r, -reverse：以相反顺序排序
    ls --help：列出这份帮助说明
            """

    def __init__(self, *args):
        self.args = args or []
        if '-A' in self.args or '-almost-all' in self.args:
            self.almost_all = True
        if '-a' in self.args or '-all' in self.args:
            self.all = True
        if '-B' in self.args or '-ignore-back-backups' in self.args:
            self.ignore_back_backups = True
        if '-r' in self.args or '-reverse' in self.args:
            self.reverse = True
        if '-l' in self.args or '-list' in self.args:
            self.list = True
        if '--help' in self.args:
            self.help = True

        self.paths = []
        path_start = None
        for arg in self.args:
            if '-' not in arg:
                path_start = args.index(arg)
                break
        if path_start is not None:
            self.paths = self.args[path_start:]

        if not len(self.paths):
            self.paths += ['.']

    def handler(self):
        if self.help:
            print(self.usage)
            return

        for path in self.paths:
            try:
                dirs = os.listdir(path)
            except FileNotFoundError as e:
                print(e)
            else:
                if self.ignore_back_backups:
                    dirs = [dir for dir in dirs if not dir.endswith('~')]
                if self.all:
                    dirs = ['.', '..'] + dirs
                if self.almost_all:
                    dirs = [dir for dir in dirs if not dir.startswith('.')]
                if self.reverse:
                    dirs.reverse()

                if self.list:
                    print('\n'.join(dirs))
                else:
                    print('  '.join(dirs))
        return