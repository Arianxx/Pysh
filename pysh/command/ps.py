from datetime import datetime
from ..manage.env import Application

app = Application()

@app.register
class ps:
    usage = """
Usage:
    ps [options]
    ps --help
            """

    def __init__(self, *args):
        self.args = args

    def handler(self):
        if '--help' in self.args:
            print(self.usage)
            return
        else:
            process = self.env['Processing'].get_records()
            print('{:<10}{:<10}{:<10}'.format('PID', 'NAME', 'TIME'))
            if len(self.args) > 0:
                pids = []
                for arg in self.args:
                    pids += [pid
                            for pid in process.keys()
                            if process[pid]['NAME'] == arg]
            else:
                pids = [pid for pid in process.keys()]

            for pid in pids:
                print('{:<10}{:<10}{:<10}'.format(
                    pid,
                    process[pid]['NAME'],
                    str(process[pid]['TIME']),
                ))
