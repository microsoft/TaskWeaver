import threading
import time
from textwrap import dedent
from typing import Any, List, Optional, Tuple

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

    def handle_message(self, session: Session, message: str) -> Optional[str]:
        def execution_thread():
            try:
                round = session.send_message(
                    message,
                    event_handler=self,
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
        counter = 0
        status_msg = "preparing"
        cur_message_buffer = ""
        cur_key = ""
        role = "TaskWeaver"
        next_role = ""

        def clear_line():
            print(ansi.clear_line(), end="\r")

        def get_ani_frame(frame: int = 0):
            frame_inx = abs(frame % 20 - 10)
            ani_frame = " " * frame_inx + "<=💡=>" + " " * (10 - frame_inx)
            return ani_frame

        last_time = 0
        while True:
            clear_line()
            with self.lock:
                for action, opt in self.pending_updates:
                    if action == "start_post":
                        role = opt
                        next_role = ""
                        print(f" ╭───< {role} >")
                    elif action == "end_post":
                        print(f" ╰──● sending message to {next_role}")
                    elif action == "send_to_update":
                        next_role = opt
                        # print(f" ├─► Reply to: {next_role}")
                    elif action == "attachment_start":
                        cur_key = opt
                        cur_message_buffer = ""
                    elif action == "attachment_add":
                        cur_message_buffer += str(opt)
                    elif action == "attachment_end":
                        if cur_key == "msg":
                            print(f" ├──● {cur_message_buffer}")
                        else:
                            print(f" ├─► [{cur_key}] {cur_message_buffer}")
                        # print(" │  ")
                    elif action == "round_error":
                        error_message(opt)

                self.pending_updates.clear()

            if self.exit_event.is_set():
                break

            click.secho(
                click.style(
                    f">>> [{role}] {status_msg} {get_ani_frame(counter)}\r",
                    fg="bright_black",
                ),
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
            if lower_message in ["help", "h", "?"]:
                self._print_help()
                return
            if lower_message == "clear":
                click.clear()
                return
            if lower_message == "reset":
                self._reset_session()
                return
            if lower_command == "load":
                file_to_load = msg[5:].strip()
                self._load_file(file_to_load)
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
                """,
            ),
        )

    def _load_file(self, file_to_load: str):
        import os

        file_path = os.path.realpath(file_to_load.strip())
        if not os.path.exists(file_path):
            error_message(f"File '{file_to_load}' not found")
            return
        self._system_message(f"Loading file '{file_to_load}'")

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
        result = updater.handle_message(self.session, input_message)
        if result is not None:
            self._assistant_message(result)

    def _assistant_message(self, message: str) -> None:
        click.secho(click.style(" TaskWeaver ", fg="white", bg="yellow"), nl=False)
        click.secho(click.style(f"▶  {message}", fg="yellow"))


def chat_taskweaver(app_dir: Optional[str] = None):
    TaskWeaverChatApp(app_dir=app_dir).run()


if __name__ == "__main__":
    chat_taskweaver()
