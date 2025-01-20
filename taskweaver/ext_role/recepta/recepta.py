from injector import inject

from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing
from taskweaver.role import Role
from taskweaver.role.role import RoleConfig, RoleEntry


class ReceptaConfig(RoleConfig):
    def _configure(self):
        self.decorator = self._get_str("decorator", "")


class Recepta(Role):
    @inject
    def __init__(
        self,
        config: ReceptaConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: RoleEntry,
    ):
        super().__init__(config, logger, tracing, event_emitter, role_entry)

    def reply(self, memory: Memory, **kwargs: ...) -> Post:
        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )

        # obtain the query from the last round
        last_post = rounds[-1].post_list[-1]

        post_proxy = self.event_emitter.create_post_proxy(self.alias)

        post_proxy.update_send_to(last_post.send_from)
        post_proxy.update_message(
            "Got it. Now, please go ahead!",
        )

        return post_proxy.end()
