from ..manage.env import Application

app = Application()

@app.register
class ps:
    usage = """
Usage:
    ps：查看所有运行中的命令。
    ps [name] [name] ...：查看给出名字的运行的命令。
    ps --help
            """

    def __init__(self, *args):
        self.args = args

    def handler(self):
        if '--help' in self.args:
            print(self.usage)
            return True
        else:
            process = self.env['Processing'].get_records()
            print('{:<10}{:<10}{:<10}{:<10}'.format('PID', 'NAME', 'BACKEND', 'TIME'))
            if len(self.args) > 0:
                pids = []
                for arg in self.args:
                    pids += [pid
                            for pid in process.keys()
                            if process[pid]['NAME'] == arg]
            else:
                pids = [pid for pid in process.keys()]

            for pid in pids:
                print('{:<10}{:<10}{:<10}{:<10}'.format(
                    pid,
                    process[pid]['NAME'],
                    str(process[pid]['instance'].backend),
                    str(process[pid]['TIME']),
                ))

        return True
