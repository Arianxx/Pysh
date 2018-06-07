# -*- coding: utf-8 -*-
from ..manage.env import Application

app = Application()


@app.register
class kill:
    help = False
    usage = """
Usage:
    kill [pid1] [pid2] ...：杀死给出的进程
    kill --help(default)：显示本帮助
            """

    def __init__(self, *args):
        self.args = args or []
        if '--help' in self.args or not self.args:
            self.help = True

    def handler(self):
        if self.help:
            print(self.usage)
        else:
            process = self.env['Processing'].get_records()
            ids = list(map(int, self.args))
            for id in ids:
                if id not in process.keys():
                    print('{} 是一个无效的pid.'.format(str(id)))
                elif not process[id]['instance'].backend:
                    print('{} 是一个前台命令，你不能终止它.'.format(str(id)))
                else:
                    try:
                        process[id]['instance'].terminate()
                    except AttributeError as e:
                        # 杀死当前阻塞的pysh进程时，会弹出AttributeError
                        print('你不能杀死阻塞中的pysh进程。请使用 exit 退出。')
                    else:
                        print('pid 为 {} 的进程 {} 已经被你终止.'.format(
                            str(id),
                            process[id]['NAME'],
                        ))

        return True
