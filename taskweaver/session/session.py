import os
import shutil
from typing import Any, Dict, List, Literal, Optional

from injector import Injector, inject

from taskweaver.code_interpreters.code_executor import CodeExecutor
from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post, Round
from taskweaver.module.event_emitter import SessionEventEmitter, SessionEventHandler
from taskweaver.planner.planner import Planner
from taskweaver.role import Role
from taskweaver.utils import import_modules_from_dir
from taskweaver.workspace.workspace import Workspace


class AppSessionConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("session")

        self.no_planner_mode = self._get_bool("no_planner_mode", False)
        self.max_internal_chat_round_num = self._get_int("max_internal_chat_round_num", 10)
        self.experience_dir = self._get_path(
            "experience_dir",
            os.path.join(self.src.app_base_path, "experience"),
        )

        self.workers = self._get_list("workers", ["code_interpreter"])

        num_code_interpreters = len([w for w in self.workers if w.startswith("code_interpreter")])
        assert num_code_interpreters == 1, (
            f"Only single code_interpreter is allowed, " f"but {num_code_interpreters} are provided."
        )


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

        self.init()

        self.round_index = 0
        self.memory = Memory(session_id=self.session_id)

        self.session_var: Dict[str, str] = {}

        self.event_emitter = self.session_injector.get(SessionEventEmitter)
        self.session_injector.binder.bind(SessionEventEmitter, self.event_emitter)

        # import all code interpreters
        import_modules_from_dir(
            os.path.join(
                self.config.src.module_base_path,
                "code_interpreters",
            ),
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

        self.worker_instances = {}
        import_modules_from_dir(
            os.path.join(
                self.config.src.module_base_path,
                "ext_roles",
            ),
        )

        for sub_cls in Role.__subclasses__():
            if sub_cls is Planner:
                continue
            role_instance = self.session_injector.get(sub_cls)
            if role_instance.name in self.config.workers:
                self.worker_instances[role_instance.get_alias()] = role_instance

        self.planner = self.session_injector.create_object(Planner, {"workers": self.worker_instances})
        self.session_injector.binder.bind(Planner, self.planner)

        self.max_internal_chat_round_num = self.config.max_internal_chat_round_num
        self.internal_chat_num = 0

        self.logger.dump_log_file(
            self,
            file_path=os.path.join(self.workspace, f"{self.session_id}.json"),
        )

    def init(self):
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        if not os.path.exists(self.execution_cwd):
            os.makedirs(self.execution_cwd)

        if not os.path.exists(self.config.experience_dir):
            os.makedirs(self.config.experience_dir)

        self.logger.info(f"Session {self.session_id} is initialized")

    def update_session_var(self, variables: Dict[str, str]):
        self.session_var.update(variables)

    def _send_text_message(self, message: str) -> Round:
        chat_round = self.memory.create_round(user_query=message)
        self.event_emitter.start_round(chat_round.id)

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
            elif recipient in self.worker_instances.keys():
                reply_post = self.worker_instances[recipient].reply(
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
            if not self.config.no_planner_mode:
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
                assert len(self.worker_instances) == 1, (
                    "Only single worker is allowed in no_planner_mode "
                    "because the user message will be sent to the worker directly."
                )
                worker_name = list(self.worker_instances.keys())[0]
                post = Post.create(
                    message=message,
                    send_from="Planner",
                    send_to=worker_name,
                )
                while True:
                    if post.send_to == "Planner":
                        reply_post = Post.create(
                            message=post.message,
                            send_from=worker_name,
                            send_to="User",
                        )
                        chat_round.add_post(reply_post)
                        break
                    else:
                        post = _send_message(worker_name, post)

            self.round_index += 1
            chat_round.change_round_state("finished")

        except Exception as e:
            import traceback

            stack_trace_str = traceback.format_exc()
            self.logger.error(stack_trace_str)
            chat_round.change_round_state("failed")
            err_message = f"Cannot process your request due to Exception: {str(e)} \n {stack_trace_str}"
            self.event_emitter.emit_error(err_message)

        finally:
            self.internal_chat_num = 0
            self.logger.dump_log_file(
                chat_round,
                file_path=os.path.join(
                    self.workspace,
                    f"{self.session_id}_{chat_round.id}.json",
                ),
            )
            self.event_emitter.end_round(chat_round.id)
            return chat_round

    def send_message(
        self,
        message: str,
        event_handler: Optional[SessionEventHandler] = None,
        files: Optional[List[Dict[Literal["name", "path", "content"], Any]]] = None,
    ) -> Round:
        message_prefix = ""
        if files is not None:
            file_names: List[str] = []
            for file_info in files:
                file_name = file_info["name"]
                file_path = file_info.get("path", None)
                file_content = file_info.get("content", None)
                file_names.append(self._upload_file(file_name, file_path, file_content))
            if len(file_names) > 0:
                message_prefix += f"files added: {', '.join(file_names)}.\n"

        with self.event_emitter.handle_events_ctx(event_handler):
            return self._send_text_message(message_prefix + message)

    def _upload_file(self, name: str, path: Optional[str] = None, content: Optional[bytes] = None) -> str:
        target_name = name.split("/")[-1]
        target_path = self.get_full_path(self.execution_cwd, target_name)
        if path is not None:
            shutil.copyfile(path, target_path)
            return target_name
        if content is not None:
            with open(target_path, "wb") as f:
                f.write(content)
            return target_name
        raise ValueError("path or file_content")

    def get_full_path(self, *file_path: str, in_execution_cwd: bool = False) -> str:
        return str(
            os.path.realpath(
                os.path.join(
                    self.workspace if not in_execution_cwd else self.execution_cwd,
                    *file_path,  # type: ignore
                ),
            ),
        )

    def stop(self) -> None:
        self.logger.info(f"Session {self.session_id} is stopped")
        self.code_executor.stop()
        for worker in self.worker_instances.values():
            worker.close()

    def to_dict(self) -> Dict[str, str]:
        return {
            "session_id": self.session_id,
            "workspace": self.workspace,
            "execution_cwd": self.execution_cwd,
        }
