from ipykernel.displayhook import ZMQShellDisplayHook


class TaskWeaverZMQShellDisplayHook(ZMQShellDisplayHook):
    def quiet(self):
        try:
            return ZMQShellDisplayHook.quiet(self)
        except Exception:
            return False
