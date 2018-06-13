"""
实现控制流的模块。
拦截待分发的命令，解析关键词，根据不同逻辑做出相应调度
"""

class ControlFlow:
    storage = {}

    @classmethod
    def register(cls, control_cls):
        cls.storage.update({
            control_cls.__name__:control_cls,
        })
        return control_cls


@ControlFlow.register
class WhileControl:
    keyword = 'while'

    def __init__(self):
        pass
