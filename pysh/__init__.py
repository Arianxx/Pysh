"""
这里提供内部命令的导入，以及一些外部工具
"""
from .command import pysh, exit, ps, history, ls, ps, cd, kill, hash, help, \
    echo
from .manage.dispatch import dispatch
from .manage.env import Application


class Pysh:
    @classmethod
    def start(cls):
        dispatch.dispatch('pysh')

class App:
    app = Application()

    register = app.register