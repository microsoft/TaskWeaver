import shutil
import threading
import time
from textwrap import TextWrapper, dedent
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import click
from colorama import ansi

from taskweaver.app.app import TaskWeaverApp
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventType, RoundEventType, SessionEventHandlerBase, SessionEventType
from taskweaver.session.session import Session


def error_message(message: str) -> None:
    click.secho(click.style(f"Error: {message}", fg="red"))


def plain_message(message: str, type: str, nl: bool = True) -> None:
    click.secho(
        click.style(
            f">>> [{type.upper()}]\n{message}",
            fg="bright_black",
        ),
        nl=nl,
    )


def user_input_message(prompt: str = "   Human  ") -> str:
    import os

    import prompt_toolkit
    import prompt_toolkit.history

    history = prompt_toolkit.history.FileHistory(
        os.path.expanduser("~/.taskweaver-history"),
    )
    session = prompt_toolkit.PromptSession[str](
        history=history,
        multiline=False,
        complete_while_typing=True,
        complete_in_thread=True,
        enable_history_search=True,
    )

    while True:
        try:
            user_input: str = session.prompt(
                prompt_toolkit.formatted_text.FormattedText(
                    [
                        ("bg:ansimagenta fg:ansiwhite", f" {prompt} "),
                        ("fg:ansimagenta", "▶"),
                        ("", "  "),
                    ],
                ),
            )
            return user_input
        except KeyboardInterrupt:
            if session.default_buffer.text == "":
                exit(0)
            continue


class TaskWeaverRoundUpdater(SessionEventHandlerBase):
    def __init__(self):
        self.exit_event = threading.Event()
        self.update_cond = threading.Condition()
        self.lock = threading.Lock()

        self.last_attachment_id = ""
        self.pending_updates: List[Tuple[str, str]] = []

        self.messages: List[Tuple[str, str]] = []
        self.response: List[str] = []
        self.result: Optional[str] = None

    def handle_session(
        self,
        type: SessionEventType,
        msg: str,
        extra: Any,
        **kwargs: Any,
    ):
        pass

    def handle_round(
        self,
        type: RoundEventType,
        msg: str,
        extra: Any,
        round_id: str,
        **kwargs: Any,
    ):
        if type == RoundEventType.round_error:
            with self.lock:
                self.pending_updates.append(("end_post", ""))
                self.pending_updates.append(("round_error", msg))

    def handle_post(
        self,
        type: PostEventType,
        msg: str,
        extra: Any,
        post_id: str,
        round_id: str,
        **kwargs: Any,
    ):
        if type == PostEventType.post_start:
            with self.lock:
                self.pending_updates.append(("start_post", extra["role"]))
        elif type == PostEventType.post_end:
            with self.lock:
                self.pending_updates.append(("end_post", ""))
        elif type == PostEventType.post_error:
            with self.lock:
                pass
        elif type == PostEventType.post_attachment_update:
            with self.lock:
                id: str = extra["id"]
                a_type: AttachmentType = extra["type"]
                is_end: bool = extra["is_end"]
                # a_extra: Any = extra["extra"]
                if id != self.last_attachment_id:
                    self.pending_updates.append(("attachment_start", a_type.name))
                    self.last_attachment_id = id
                self.pending_updates.append(("attachment_add", msg))
                if is_end:
                    self.last_attachment_id = ""
                    self.pending_updates.append(("attachment_end", ""))
        elif type == PostEventType.post_send_to_update:
            with self.lock:
                self.pending_updates.append(("send_to_update", extra["role"]))
        elif type == PostEventType.post_message_update:
            with self.lock:
                if self.last_attachment_id != "msg":
                    self.pending_updates.append(("attachment_start", "msg"))
                    self.last_attachment_id = "msg"
                self.pending_updates.append(("attachment_add", msg))
                if extra["is_end"]:
                    self.last_attachment_id = ""
                    self.pending_updates.append(("attachment_end", ""))
        elif type == PostEventType.post_status_update:
            with self.lock:
                self.pending_updates.append(("status_update", msg))

    def handle_message(
        self,
        session: Session,
        message: str,
        files: List[Dict[Literal["name", "path", "content"], str]],
    ) -> Optional[str]:
        def execution_thread():
            try:
                round = session.send_message(
                    message,
                    event_handler=self,
                    files=files,
                )
                last_post = round.post_list[-1]
                if last_post.send_to == "User":
                    self.result = last_post.message
            except Exception as e:
                self.response.append("Error")
                raise e
            finally:
                self.exit_event.set()
                with self.update_cond:
                    self.update_cond.notify_all()

        t_ui = threading.Thread(target=lambda: self._animate_thread(), daemon=True)
        t_ex = threading.Thread(target=execution_thread, daemon=True)

        t_ui.start()
        t_ex.start()
        exit_no_wait: bool = False
        try:
            while True:
                self.exit_event.wait(0.1)
                if self.exit_event.is_set():
                    break
        except KeyboardInterrupt:
            error_message("Interrupted by user")
            exit_no_wait = True

            # keyboard interrupt leave the session in unknown state, exit directly
            exit(1)
        finally:
            self.exit_event.set()
            with self.update_cond:
                self.update_cond.notify_all()
            try:
                t_ex.join(0 if exit_no_wait else 1)
                t_ui.join(1)
            except Exception:
                pass

        return self.result

    def _animate_thread(self):
        # get terminal width
        terminal_column = shutil.get_terminal_size().columns
        counter = 0
        status_msg = "preparing"
        cur_message_buffer = ""
        cur_key = ""
        role = "TaskWeaver"
        next_role = ""

        def style_line(s: str):
            return click.style(s, fg="blue")

        def style_role(s: str):
            return click.style(s, fg="bright_yellow", underline=True)

        def style_key(s: str):
            return click.style(s, fg="bright_cyan")

        def style_msg(s: str):
            return click.style(s, fg="bright_black")

        def style_msg_main(s: str):
            return click.style(s, fg="white")

        wrapper = TextWrapper(
            width=terminal_column,
            initial_indent=" ├─► ",
            subsequent_indent=" │   ",
            break_long_words=True,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=False,
        )

        def wrap_message(
            message: str,
            init_indent: str = " │   ",
            seq_indent: str = " │   ",
            key: Optional[str] = None,
            styler: Callable[[str], str] = style_msg,
        ):
            result: List[str] = []
            is_first = True
            seq_indent_style = style_line(seq_indent)
            for line in message.split("\n"):
                if is_first:
                    cur_init = init_indent
                    cur_init_style = style_line(cur_init)
                    if key is not None:
                        cur_init += f"[{key}]"
                        cur_init_style += style_line("[") + style_key(key) + style_line("]")
                    is_first = False
                else:
                    cur_init = seq_indent
                    cur_init_style = seq_indent_style
                wrapper.initial_indent = cur_init
                wrapper.subsequent_indent = seq_indent

                if line == "":
                    result.append(cur_init_style)
                else:
                    lines = wrapper.wrap(line)
                    for i, l in enumerate(lines):
                        if i == 0:
                            result.append(cur_init_style + styler(l[len(cur_init) :]))
                        else:
                            result.append(
                                seq_indent_style + styler(l[len(seq_indent) :]),
                            )

            return "\n".join(result)

        def clear_line():
            print(ansi.clear_line(), end="\r")

        def get_ani_frame(frame: int = 0):
            frame_inx = abs(frame % 20 - 10)
            ani_frame = " " * frame_inx + "<=💡=>" + " " * (10 - frame_inx)
            return ani_frame

        def format_status_message(limit: int):
            incomplete_suffix = "..."
            incomplete_suffix_len = len(incomplete_suffix)
            if len(cur_message_buffer) == 0:
                if len(status_msg) > limit - 1:
                    return f" {status_msg[(limit - incomplete_suffix_len - 1):]}{incomplete_suffix}"
                return " " + status_msg

            cur_key_display = style_line("[") + style_key(cur_key) + style_line("]")
            cur_key_len = len(cur_key) + 2  # with extra bracket
            cur_message_buffer_norm = cur_message_buffer.replace("\n", " ").replace(
                "\r",
                " ",
            )

            if len(cur_message_buffer_norm) < limit - cur_key_len - 1:
                return f"{cur_key_display} {cur_message_buffer_norm}"

            status_msg_len = limit - cur_key_len - incomplete_suffix_len
            return f"{cur_key_display}{incomplete_suffix}{cur_message_buffer_norm[-status_msg_len:]}"

        last_time = 0
        while True:
            clear_line()
            with self.lock:
                for action, opt in self.pending_updates:
                    if action == "start_post":
                        role = opt
                        next_role = ""
                        status_msg = "initializing"
                        click.secho(
                            style_line(
                                " ╭───<",
                            )
                            + style_role(
                                f" {role} ",
                            )
                            + style_line(">"),
                        )
                    elif action == "end_post":
                        status_msg = "finished"
                        click.secho(
                            style_line(" ╰──●")
                            + style_msg(" sending message to ")
                            + style_role(
                                next_role,
                            ),
                        )
                    elif action == "send_to_update":
                        next_role = opt
                    elif action == "attachment_start":
                        cur_key = opt
                        cur_message_buffer = ""
                    elif action == "attachment_add":
                        cur_message_buffer += str(opt)
                    elif action == "attachment_end":
                        if cur_key == "msg":
                            click.secho(
                                wrap_message(
                                    cur_message_buffer,
                                    " ├──● ",
                                    styler=style_msg_main,
                                ),
                            )
                        else:
                            msg_sep = "\n" if cur_message_buffer.find("\n") >= 0 else " "
                            click.secho(
                                wrap_message(
                                    f"{msg_sep}{cur_message_buffer}",
                                    " ├─► ",
                                    key=cur_key,
                                ),
                            )
                        cur_message_buffer = ""
                    elif action == "round_error":
                        error_message(opt)
                    elif action == "status_update":
                        status_msg = opt

                self.pending_updates.clear()

            if self.exit_event.is_set():
                break

            cur_message_prefix: str = " TaskWeaver "
            cur_ani_frame = get_ani_frame(counter)
            cur_message_display_len = (
                terminal_column
                - len(cur_message_prefix)
                - 2  # separator for cur message prefix
                - len(role)
                - 2  # bracket for role
                - len(cur_ani_frame)
                - 2  # extra size for emoji in ani
            )

            cur_message_display = format_status_message(cur_message_display_len)

            click.secho(
                click.style(cur_message_prefix, fg="white", bg="yellow")
                + click.style("▶ ", fg="yellow")
                + style_line("[")
                + style_role(role)
                + style_line("]")
                + style_msg(cur_message_display)
                + style_msg(cur_ani_frame)
                + "\r",
                # f">>> [{style_role(role)}] {status_msg} {get_ani_frame(counter)}\r",
                nl=False,
            )

            cur_time = time.time()
            if cur_time - last_time < 0.2:
                # skip animation update
                continue

            with self.lock:
                counter += 1
                last_time = cur_time

            with self.update_cond:
                self.update_cond.wait(0.2 - (cur_time - last_time))


class TaskWeaverChatApp(SessionEventHandlerBase):
    def __init__(self, app_dir: Optional[str] = None):
        self.app = TaskWeaverApp(app_dir=app_dir, use_local_uri=True)
        self.session = self.app.get_session()
        self.pending_files: List[Dict[Literal["name", "path", "content"], Any]] = []

    def run(self):
        self._reset_session(first_session=True)
        while True:
            user_input = user_input_message()
            self._process_user_input(user_input)

    def _process_user_input(self, user_input: str) -> None:
        msg = user_input.strip()
        if msg == "":
            error_message("Empty input, please try again")
            return

        if msg.startswith("/"):
            lower_message = msg.lower()
            lower_command = lower_message.lstrip("/").split(" ")[0]
            if lower_command in ["exit", "bye", "quit"]:
                exit(0)
            if lower_command in ["help", "h", "?"]:
                self._print_help()
                return
            if lower_command == "clear":
                click.clear()
                return
            if lower_command == "reset":
                self._reset_session()
                return
            if lower_command in ["load", "file"]:
                file_to_load = msg[5:].strip()
                self._load_file(file_to_load)
                return
            if lower_command == "save":
                self._save_memory()
                return
            error_message(f"Unknown command '{msg}', please try again")
            return

        self._handle_message(msg)

    def _print_help(self):
        self._system_message(
            dedent(
                """
                TaskWeaver Chat Console
                -----------------------
                /load <file>: load a file
                /reset: reset the session
                /clear: clear the console
                /exit: exit the chat console
                /help: print this help message
                /save: save the memory for experience reuse
                """,
            ),
        )

    def _save_memory(self):
        self.session.memory.save_experience(exp_dir=self.session.config.experience_dir)

    def _load_file(self, file_to_load: str):
        import os

        file_path = os.path.realpath(file_to_load.strip())
        file_name = os.path.basename(file_path)
        if not os.path.exists(file_path):
            error_message(f"File '{file_to_load}' not found")
            return
        self.pending_files.append(
            {"name": file_name, "path": file_path},
        )
        self._system_message(
            f"Added '{file_name}' for loading, type message to send",
        )

    def _reset_session(self, first_session: bool = False):
        if not first_session:
            self._system_message("--- new session starts ---")
            self.session = self.app.get_session()

        self._assistant_message(
            "I am TaskWeaver, an AI assistant. To get started, could you please enter your request?",
        )

    def _system_message(self, message: str):
        click.secho(message, fg="bright_black")

    def _handle_message(self, input_message: str):
        updater = TaskWeaverRoundUpdater()
        result = updater.handle_message(
            self.session,
            input_message,
            files=self.pending_files,
        )
        self.pending_files = []
        if result is not None:
            self._assistant_message(result)

    def _assistant_message(self, message: str) -> None:
        click.secho(click.style(" TaskWeaver ", fg="white", bg="yellow"), nl=False)
        click.secho(click.style(f"▶  {message}", fg="yellow"))


def chat_taskweaver(app_dir: Optional[str] = None):
    TaskWeaverChatApp(app_dir=app_dir).run()


if __name__ == "__main__":
    chat_taskweaver()
