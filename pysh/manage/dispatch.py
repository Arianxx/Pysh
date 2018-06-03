"""
Dispatch接受解析之后的参数，将参数分发给应用执行，并执行环境需要的其它操作。
"""
from multiprocessing import Process
from .env import Application, Processing, History

apps = Application.app

class Task(Process):
    """
    包装真正的命令。
    """
    def __init__(self, app, *args):
        super().__init__()
        self.app = app
        self.args = args
        self.name = self.app.__class__.__name__
        self.daemon = True

        self._task = self.app(*self.args)

        # 绑定当前环境到应用，以便多进程下能够访问
        self._task.env = {
            'app': Application.app,
            'process': Processing.process,
            'history': History.history,
        }

        # 用这个代替pid，是因为前台命令没有pid
        self.id = self._identity[0]

    def run(self):
        if self.daemon:
            Application.app = self._task.env['app']
            Processing.process = self._task.env['process']
            History.history = self._task.env['history']

        self._task.env.update(
            Application = Application,
            Processing = Processing,
            History = History,
        )

        Processing.record(self)

        try:
            self._task.handler()
        except EOFError as e:
            # 后台命令具有交互功能，会弹出EOFError，因为子进程中关闭了stdin
            print('\n命令退出，后台程序不能交互！')
        except Exception as e:
            raise e
        finally:
            # 清理记录
            Processing.remove(self.id)

class Dispatch:
    def __init__(self):
        pass

    def _thread(self, app, *args):
        """
        后台命令就新建一个进程。

        :param app: 要启动的app类
        :param args: 命令的参数
        :return: None
        """
        task = Task(app, *args)
        task.start()
        task.join()

    def _front(self, app, *args):
        """
        前台程序直接手动启动。

        :param app: 要启动的app类
        :param args: 命令的参数
        :return: None
        """
        task = Task(app, *args)
        task.daemon = False
        task.run()

    @History.history_recorder
    def dispatch(self, command, *args, daemon):
        app = apps.get(command, None)

        if app:
            if daemon:
                return_value = self._thread(app, *args)
            else:
                return_value = self._front(app, *args)
        else:
            print('{}: command not found'.format(command))
            return_value = None

        return return_value

dispatch = Dispatch()