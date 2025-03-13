import os
import shutil
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from injector import Injector, inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post, Round
from taskweaver.module.event_emitter import SessionEventEmitter, SessionEventHandler
from taskweaver.module.tracing import Tracing, tracing_decorator, tracing_decorator_non_class
from taskweaver.planner.planner import Planner
from taskweaver.role.role import RoleRegistry
from taskweaver.workspace.workspace import Workspace


class AppSessionConfig(ModuleConfig):
    def _configure(self) -> None:
        self._set_name("session")

        self.max_internal_chat_round_num = self._get_int("max_internal_chat_round_num", 10)
        self.experience_dir = self._get_path(
            "experience_dir",
            os.path.join(self.src.app_base_path, "experience"),
        )

        self.roles = self._get_list("roles", ["planner", "code_interpreter", "recepta", "image_reader"])

        assert len(self.roles) > 0, "At least one role should be provided."
        self.num_code_interpreters = len([w for w in self.roles if w.startswith("code_interpreter")])
        assert (
            self.num_code_interpreters <= 1
        ), f"Only single code_interpreter is allowed, but {self.num_code_interpreters} are provided."


@dataclass
class SessionMetadata:
    session_id: str
    workspace: str
    execution_cwd: str


class Session:
    @inject
    def __init__(
        self,
        session_id: str,
        workspace: Workspace,
        app_injector: Injector,
        logger: TelemetryLogger,
        tracing: Tracing,
        config: AppSessionConfig,  # TODO: change to SessionConfig
        role_registry: RoleRegistry,
    ) -> None:
        """
        Initialize the session.
        :param session_id: The session ID.
        :param workspace: The workspace.
        :param app_injector: The app injector.
        :param logger: The logger.
        :param tracing: The tracing.
        :param config: The configuration.
        :param role_registry: The role registry.
        """
        assert session_id is not None, "session_id must be provided"
        self.logger = logger
        self.tracing = tracing
        self.session_injector = app_injector.create_child_injector()
        self.config = config

        self.session_id: str = session_id

        self.workspace = workspace.get_session_dir(self.session_id)
        self.execution_cwd = os.path.join(self.workspace, "cwd")

        self.metadata = SessionMetadata(
            session_id=self.session_id,
            workspace=self.workspace,
            execution_cwd=self.execution_cwd,
        )
        self.session_injector.binder.bind(SessionMetadata, self.metadata)

        self._init()

        self.round_index = 0
        self.memory = Memory(session_id=self.session_id)

        self.session_var: Dict[str, str] = {}

        self.event_emitter = self.session_injector.get(SessionEventEmitter)
        self.session_injector.binder.bind(SessionEventEmitter, self.event_emitter)

        self.role_registry = role_registry
        self.worker_instances = {}
        for role_name in self.config.roles:
            if role_name == "planner":
                continue
            if role_name not in role_registry.get_role_name_list():
                raise ValueError(f"Unknown role {role_name}")
            role_entry = self.role_registry.get(role_name)
            role_instance = self.session_injector.create_object(
                role_entry.module,
                {
                    "role_entry": role_entry,
                },
            )
            self.session_injector.binder.bind(role_entry.module, role_instance)
            self.worker_instances[role_instance.get_alias()] = role_instance

        if "planner" in self.config.roles:
            self.planner = self.session_injector.create_object(
                Planner,
                {
                    "workers": self.worker_instances,
                },
            )
            self.session_injector.binder.bind(Planner, self.planner)

        self.max_internal_chat_round_num = self.config.max_internal_chat_round_num
        self.internal_chat_num = 0

        self.logger.dump_log_file(
            self,
            file_path=os.path.join(self.workspace, f"{self.session_id}.json"),
        )

    def _init(self):
        """
        Initialize the session by creating the workspace and execution cwd.
        """
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        if not os.path.exists(self.execution_cwd):
            os.makedirs(self.execution_cwd)

        if not os.path.exists(self.config.experience_dir):
            os.makedirs(self.config.experience_dir)

        self.logger.info(f"Session {self.session_id} is initialized")

    @tracing_decorator
    def update_session_var(
        self,
        variables: Dict[str, str],
    ):
        """
        Update the session variables.
        :param variables: The variables to update.
        """
        assert self.config.num_code_interpreters > 0, "No code_interpreter role is provided."
        self.session_var.update(variables)
        # get the alias of the code_interpreter
        code_interpreter_role_name = [w for w in self.config.roles if w.startswith("code_interpreter")][0]
        code_interpreter_role_entry = self.role_registry.get(code_interpreter_role_name)
        code_interpreter_instance = self.worker_instances[code_interpreter_role_entry.alias]
        code_interpreter_instance.update_session_variables(variables)
        self.logger.info(f"Update session variables: {variables} for {code_interpreter_instance.get_alias()}")

    @tracing_decorator
    def _send_text_message(
        self,
        message: str,
    ) -> Round:
        chat_round = self.memory.create_round(user_query=message)

        self.tracing.set_span_attribute("round_id", chat_round.id)
        self.tracing.set_span_attribute("round_index", self.round_index)
        self.tracing.set_span_attribute("message", message)

        self.event_emitter.start_round(chat_round.id)

        @tracing_decorator_non_class
        def _send_message(recipient: str, post: Post) -> Post:
            self.tracing.set_span_attribute("in.from", post.send_from)
            self.tracing.set_span_attribute("in.recipient", recipient)
            self.tracing.set_span_attribute("in.message", post.message)
            self.tracing.set_span_attribute("in.attachments", str(post.attachment_list))

            chat_round.add_post(post)

            if recipient == "Planner":
                reply_post = self.planner.reply(
                    self.memory,
                    prompt_log_path=os.path.join(
                        self.workspace,
                        f"planner_prompt_log_{chat_round.id}_{post.id}.json",
                    ),
                )
            elif recipient in self.worker_instances.keys():
                reply_post = self.worker_instances[recipient].reply(
                    self.memory,
                    prompt_log_path=os.path.join(
                        self.workspace,
                        f"code_generator_prompt_log_{chat_round.id}_{post.id}.json",
                    ),
                )
            else:
                raise Exception(f"Unknown recipient {recipient}")

            return reply_post

        try:
            if "planner" in self.config.roles and len(self.worker_instances) > 0:
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
                    "Only single worker role (e.g., code_interpreter) is allowed in no-planner mode "
                    "because the user message will be sent to the worker role directly."
                )
                worker_name = list(self.worker_instances.keys())[0]
                post = Post.create(
                    message=message,
                    send_from="Planner",
                    send_to=worker_name,
                )
                while True:
                    if post.send_to == "Planner":
                        # add the original message to the chat round
                        chat_round.add_post(post)
                        # create a reply post
                        reply_post = Post.create(
                            message=post.message,
                            send_from="Planner",
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

            self.tracing.set_span_status("ERROR", err_message)
            self.tracing.set_span_exception(e)
            self.event_emitter.emit_error(err_message)

        finally:
            self.tracing.set_span_attribute("internal_chat_num", self.internal_chat_num)

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

    @tracing_decorator
    def send_message(
        self,
        message: str,
        event_handler: Optional[SessionEventHandler] = None,
        files: Optional[List[Dict[Literal["name", "path", "content"], Any]]] = None,
    ) -> Round:
        """
        Send a message.
        :param message: The message.
        :param event_handler: The event handler.
        :param files: The files.
        :return: The chat round.
        """
        # init span with session_id
        self.tracing.set_span_attribute("session_id", self.session_id)
        self.tracing.set_span_attribute("message", message)
        self.tracing.set_span_attribute("files", str(files))

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
            chat_round = self._send_text_message(message_prefix + message)

            self.tracing.set_span_attribute("round_id", chat_round.id)
            if chat_round.state != "finished":
                self.tracing.set_span_status("ERROR", "Chat round is not finished successfully.")
            else:
                self.tracing.set_span_attribute("reply_to_user", chat_round.post_list[-1].message)

            return chat_round

    @tracing_decorator
    def _upload_file(self, name: str, path: Optional[str] = None, content: Optional[bytes] = None) -> str:
        target_name = name.split("/")[-1]
        target_path = self._get_full_path(self.execution_cwd, target_name)
        self.tracing.set_span_attribute("target_path", target_path)
        if path is not None:
            shutil.copyfile(path, target_path)
            return target_name
        if content is not None:
            with open(target_path, "wb") as f:
                f.write(content)
            return target_name

        self.tracing.set_span_status("ERROR", "path or file_content must be provided")
        raise ValueError("path or file_content")

    def _get_full_path(
        self,
        *file_path: str,
        in_execution_cwd: bool = False,
    ) -> str:
        return str(
            os.path.realpath(
                os.path.join(
                    self.workspace if not in_execution_cwd else self.execution_cwd,
                    *file_path,  # type: ignore
                ),
            ),
        )

    @tracing_decorator
    def stop(self) -> None:
        """
        Stop the session.
        This function must be called before the session exits.
        """
        self.logger.info(f"Session {self.session_id} is stopped")
        for worker in self.worker_instances.values():
            worker.close()

    def to_dict(self) -> Dict[str, str]:
        return {
            "session_id": self.session_id,
            "workspace": self.workspace,
            "execution_cwd": self.execution_cwd,
        }
