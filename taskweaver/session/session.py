import os
import shutil
from typing import Dict, Optional

from injector import Injector, inject

from taskweaver.code_interpreter import CodeInterpreter, CodeInterpreterPluginOnly
from taskweaver.code_interpreter.code_executor import CodeExecutor
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post, Round
from taskweaver.module.event_emitter import SessionEventEmitter, SessionEventHandler
from taskweaver.planner.planner import Planner
from taskweaver.workspace.workspace import Workspace


class AppSessionConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("session")

        self.code_interpreter_only = self._get_bool("code_interpreter_only", False)
        self.max_internal_chat_round_num = self._get_int("max_internal_chat_round_num", 10)
        self.plugin_only_mode = self._get_bool("plugin_only_mode", False)


class Session:
    @inject
    def __init__(
        self,
        session_id: str,
        workspace: Workspace,
        app_injector: Injector,
        logger: TelemetryLogger,
        config: AppSessionConfig,  # TODO: change to SessionConfig
    ) -> None:
        assert session_id is not None, "session_id must be provided"
        self.logger = logger
        self.session_injector = app_injector.create_child_injector()

        self.config = config

        self.session_id: str = session_id

        self.workspace = workspace.get_session_dir(self.session_id)
        self.execution_cwd = os.path.join(self.workspace, "cwd")

        self.round_index = 0
        self.memory = Memory(session_id=self.session_id)

        self.session_var: Dict[str, str] = {}

        self.planner = self.session_injector.create_object(
            Planner,
            {
                "plugin_only": self.config.plugin_only_mode,
            },
        )
        self.code_executor = self.session_injector.create_object(
            CodeExecutor,
            {
                "session_id": self.session_id,
                "workspace": self.workspace,
                "execution_cwd": self.execution_cwd,
            },
        )
        self.session_injector.binder.bind(CodeExecutor, self.code_executor)
        if self.config.plugin_only_mode:
            self.code_interpreter = self.session_injector.get(CodeInterpreterPluginOnly)
        else:
            self.code_interpreter = self.session_injector.get(CodeInterpreter)
        self.event_emitter = self.session_injector.get(SessionEventEmitter)

        self.max_internal_chat_round_num = self.config.max_internal_chat_round_num
        self.internal_chat_num = 0

        self.init()

        self.logger.dump_log_file(
            self,
            file_path=os.path.join(self.workspace, f"{self.session_id}.json"),
        )

    def init(self):
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        if not os.path.exists(self.execution_cwd):
            os.makedirs(self.execution_cwd)

        self.logger.info(f"Session {self.session_id} is initialized")

    def update_session_var(self, variables: Dict[str, str]):
        self.session_var.update(variables)

    def _send_text_message(self, message: str) -> Round:
        chat_round = self.memory.create_round(user_query=message)

        def _send_message(recipient: str, post: Post) -> Post:
            chat_round.add_post(post)

            use_back_up_engine = True if recipient == post.send_from else False
            self.logger.info(f"Use back up engine: {use_back_up_engine}")

            if recipient == "Planner":
                reply_post = self.planner.reply(
                    self.memory,
                    prompt_log_path=os.path.join(
                        self.workspace,
                        f"planner_prompt_log_{chat_round.id}_{post.id}.json",
                    ),
                    use_back_up_engine=use_back_up_engine,
                )
            elif recipient == "CodeInterpreter":
                reply_post = self.code_interpreter.reply(
                    self.memory,
                    prompt_log_path=os.path.join(
                        self.workspace,
                        f"code_generator_prompt_log_{chat_round.id}_{post.id}.json",
                    ),
                    use_back_up_engine=use_back_up_engine,
                )
            else:
                raise Exception(f"Unknown recipient {recipient}")

            return reply_post

        try:
            if not self.config.code_interpreter_only:
                post = Post.create(message=message, send_from="User", send_to="Planner")
                while True:
                    post = _send_message(post.send_to, post)
                    self.logger.info(
                        f"{post.send_from} talk to {post.send_to}: {post.message}",
                    )
                    self.internal_chat_num += 1
                    if post.send_to == "User":
                        chat_round.add_post(post)
                        self.internal_chat_num = 0
                        break
                    if self.internal_chat_num >= self.max_internal_chat_round_num:
                        raise Exception(
                            f"Internal chat round number exceeds the limit of {self.max_internal_chat_round_num}",
                        )
            else:
                post = Post.create(
                    message=message,
                    send_from="Planner",
                    send_to="CodeInterpreter",
                )
                post = _send_message("CodeInterpreter", post)
                self.event_emitter.emit_compat("final_reply_message", post.message)

            self.round_index += 1
            chat_round.change_round_state("finished")

        except Exception as e:
            import traceback

            stack_trace_str = traceback.format_exc()
            self.logger.error(stack_trace_str)
            chat_round.change_round_state("failed")
            err_message = f"Cannot process your request due to Exception: {str(e)} \n {stack_trace_str}"
            self.event_emitter.emit_compat("error", err_message)

        finally:
            self.internal_chat_num = 0
            self.logger.dump_log_file(
                chat_round,
                file_path=os.path.join(
                    self.workspace,
                    f"{self.session_id}_{chat_round.id}.json",
                ),
            )
            return chat_round

    def send_message(
        self,
        message: str,
        event_handler: Optional[SessionEventHandler] = None,
    ) -> Round:
        with self.event_emitter.handle_events_ctx(event_handler):
            return self._send_text_message(message)

    def send_file(
        self,
        file_name: str,
        file_path: str,
        event_handler: Optional[SessionEventHandler] = None,
    ) -> Round:
        with self.event_emitter.handle_events_ctx(event_handler):
            file_full_path = self.get_full_path(self.execution_cwd, file_name)
            if os.path.exists(file_full_path):
                os.remove(file_full_path)
                message = f'reload file "{file_name}"'
            else:
                message = f'load file "{file_name}"'

            shutil.copyfile(file_path, file_full_path)

            return self._send_text_message(message)

    def get_full_path(self, *file_path: str, in_execution_cwd: bool = False) -> str:
        return str(
            os.path.realpath(
                os.path.join(
                    self.workspace if not in_execution_cwd else self.execution_cwd,
                    *file_path,  # type: ignore
                ),
            ),
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "session_id": self.session_id,
            "workspace": self.workspace,
            "execution_cwd": self.execution_cwd,
        }
