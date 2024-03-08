from injector import inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.role import Role


class EchoConfig(ModuleConfig):
    def _configure(self):
        self._set_name("echo")


class Echo(Role):
    @inject
    def __init__(
        self,
        config: EchoConfig,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
    ):
        super().__init__(config, logger, event_emitter)

    def reply(self, memory: Memory, **kwargs) -> Post:
        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )

        # obtain the query from the last round
        last_post = rounds[-1].post_list[-1]

        post_proxy = self.event_emitter.create_post_proxy(self.alias)

        post_proxy.update_send_to(last_post.send_from)
        post_proxy.update_message(last_post.message)

        return post_proxy.end()
