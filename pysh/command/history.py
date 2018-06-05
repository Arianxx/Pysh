from ..manage.env import Application

app = Application()

@app.register
class history:
    num = None
    maxlen = None
    new_maxlen = None
    clear = None
    clear_num = None
    help = None
    usage = """
Usage:
    history [num]：查看num条数量的历史命令，num默认为100
    history --maxlen [num]：如果没有num，查看能容纳的最大历史数量；如果有num，更新maxlen为num
    history --clear [num]：清空最近num条数量的历史记录，num默认为maxlen
    history --help: 显示这条帮助信息
            """

    def __init__(self, *args):
        self.args = args

        if '--help' in self.args:
            self.help = True
        elif '--maxlen' in self.args:
            self.maxlen = True
            if len(self.args) > 1:
                maxlen_index = self.args.index('--maxlen')
                self.new_maxlen = self.args[maxlen_index + 1]
        elif '--clear' in self.args:
            self.clear = True
            if len(self.args) > 1:
                clear_num_index = self.args.index('--clear')
                self.clear_num = self.args[clear_num_index + 1]
        else:
            if len(self.args) > 0:
                try:
                    self.num = int(self.args[0])
                except ValueError as e:
                    print(e)
                    self.num = 0

    def handler(self):
        History = self.env['History']

        if self.help:
            print(self.usage)
        elif self.maxlen:
            if self.new_maxlen is not None:
                History.new_maxlen(self.new_maxlen)
            else:
                print(History.maxlen())
        elif self.clear:
            if self.clear_num is not None:
                for _ in range(self.clear_num):
                    History.history.pop()
            else:
                History.history.clear()
        else:
            if self.num is not None:
                length = len(History.history)
                for index in range(length, length - self.num, -1):
                    print(History.history[index-1])
            else:
                for h in History.history:
                    print(h)

        return True
