import os

from injector import inject

from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.module.event_emitter import SessionEventEmitter
from taskweaver.module.tracing import Tracing
from taskweaver.role import Role
from taskweaver.role.role import RoleConfig, RoleEntry
from taskweaver.utils import read_yaml


class WebExplorerConfig(RoleConfig):
    def _configure(self):
        self.config_file_path = self._get_str(
            "prompt_file_path",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "web_explorer_config.yaml",
            ),
        )


class WebExplorer(Role):
    @inject
    def __init__(
        self,
        config: WebExplorerConfig,
        logger: TelemetryLogger,
        tracing: Tracing,
        event_emitter: SessionEventEmitter,
        role_entry: RoleEntry,
    ):
        super().__init__(config, logger, tracing, event_emitter, role_entry)

        self.logger = logger
        self.config = config
        self.vision_planner: VisionPlanner = None
        self.driver: SeleniumDriver = None

    def initialize(self):
        try:
            from taskweaver.ext_role.web_explorer.driver import SeleniumDriver
            from taskweaver.ext_role.web_explorer.planner import VisionPlanner
            
            config = read_yaml(self.config.config_file_path)
            GPT4V_KEY = os.environ.get("GPT4V_KEY")
            GPT4V_ENDPOINT = os.environ.get("GPT4V_ENDPOINT")
            self.driver = SeleniumDriver(
                chrome_driver_path=os.environ.get("CHROME_DRIVER_PATH"),
                chrome_executable_path=os.environ.get("CHROME_EXECUTABLE_PATH"),
                mobile_emulation=False,
                js_script=config["js_script"],
            )
            self.vision_planner = VisionPlanner(
                api_key=GPT4V_KEY,
                endpoint=GPT4V_ENDPOINT,
                driver=self.driver,
                prompt=config["prompt"],
            )
        except Exception as e:
            if self.driver is not None:
                self.driver.quit()
            raise Exception(f"Failed to initialize the plugin due to: {e}")

    def reply(self, memory: Memory, **kwargs) -> Post:
        if self.vision_planner is None:
            self.initialize()

        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )
        last_post = rounds[-1].post_list[-1]
        post_proxy = self.event_emitter.create_post_proxy(self.alias)
        post_proxy.update_send_to(last_post.send_from)
        try:
            self.vision_planner.get_objective_done(
                objective=last_post.message,
                post_proxy=post_proxy,
            )
        except Exception as e:
            post_proxy.update_message(
                f"Failed to achieve the objective due to {e}. " "Please check the log for more details.",
            )

        return post_proxy.end()

    def close(self) -> None:
        if self.driver is not None:
            self.driver.quit()
        super().close()
