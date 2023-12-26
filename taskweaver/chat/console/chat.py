import threading
import time
from textwrap import dedent
from typing import Any, List, Optional, Tuple

import click
from colorama import ansi

from taskweaver.app.app import TaskWeaverApp
from taskweaver.module.event_emitter import PostEventType, RoundEventType, SessionEventHandlerBase, SessionEventType


def error_message(message: str) -> None:
    click.secho(click.style(f"Error: {message}", fg="red"))


def assistant_message(message: str) -> None:
    click.secho(click.style(f"TaskWeaver: {message}", fg="yellow"))


def plain_message(message: str, type: str, nl: bool = True) -> None:
    click.secho(
        click.style(
            f">>> [{type.upper()}]\n{message}",
            fg="bright_black",
        ),
        nl=nl,
    )


def thought_animate(message: str, type: str = " 🐙 ", frame: int = 0):
    frame_inx = abs(frame % 20 - 10)
    ani_frame = " " * frame_inx + "<=💡=>" + " " * (10 - frame_inx)
    message = f"{message} {ani_frame}\r"
    click.secho(
        click.style(
            f">>> [{type}] {message}",
            fg="bright_black",
        ),
        nl=False,
    )


def user_input_message(prompt: str = "Human") -> str:
    import os

    import prompt_toolkit
    import prompt_toolkit.history

    history = prompt_toolkit.history.FileHistory(
        os.path.expanduser("~/.taskweaver-history"),
    )
    session = prompt_toolkit.PromptSession[str](
        history=history,
        multiline=False,
        wrap_lines=True,
        complete_while_typing=True,
        complete_in_thread=True,
        enable_history_search=True,
    )

    user_input: str = session.prompt(
        prompt_toolkit.formatted_text.FormattedText(
            [
                ("ansimagenta", f"{prompt}: "),
            ],
        ),
    )
    return user_input


class TaskWeaverChatApp(SessionEventHandlerBase):
    def __init__(self, app_dir: Optional[str] = None):
        self.app = TaskWeaverApp(app_dir=app_dir, use_local_uri=True)
        self.session = self.app.get_session()

    def run(self):
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
            if lower_message == "/exit":
                exit(0)
            if lower_message == "/help":
                self._print_help()
                return
            if lower_message == "/clear":
                click.clear()
                return
            if lower_message == "/reset":
                self.session = self.app.get_session()
                return
            if lower_message.startswith("/load"):
                file_to_load = msg[5:].strip()
                self._load_file(file_to_load)
                return
            error_message(f"Unknown command '{msg}', please try again")

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
        self._system_message(f"Loading file '{file_to_load}'")

    def _reset_session(self, first_session: bool = False):
        if not first_session:
            self._system_message("--- new session starts ---")
            self.session = self.app.get_session()

        assistant_message(
            "I am TaskWeaver, an AI assistant. To get started, could you please enter your request?",
        )

    def _system_message(self, message: str):
        click.secho(message, fg="gray")

    def _handle_message(self, input_message: str):
        exit_event = threading.Event()
        lock = threading.Lock()
        messages: List[Tuple[str, str]] = []
        response: List[str] = []

        def execution_thread():
            def event_handler(type: str, msg: str):
                with lock:
                    messages.append((type, msg))

            event_handler("stage", "starting")
            try:
                self.session.send_message(
                    input_message,
                    event_handler=self,
                )
                response.append("Finished")
                exit_event.set()
            except Exception as e:
                response.append("Error")
                raise e

        def ani_thread():
            counter = 0
            stage = "preparing"

            def clear_line():
                print(ansi.clear_line(), end="\r")

            def process_messages(stage: str):
                if len(messages) == 0:
                    return stage

                clear_line()
                for type, msg in messages:
                    if type == "stage":
                        stage = msg
                    elif type == "final_reply_message":
                        assistant_message(msg)
                    elif type == "error":
                        error_message(msg)
                    else:
                        plain_message(msg, type=type)
                messages.clear()
                return stage

            while True:
                with lock:
                    stage = process_messages(stage)

                if len(response) > 0:
                    clear_line()
                    break
                with lock:
                    thought_animate(stage + "...", frame=counter)
                    counter += 1
                time.sleep(0.2)

        t_ex = threading.Thread(target=execution_thread, daemon=True)
        t_ui = threading.Thread(target=ani_thread, daemon=True)

        t_ui.start()
        t_ex.start()

        try:
            while True:
                exit_event.wait(0.1)
                if exit_event.is_set():
                    break
        except KeyboardInterrupt:
            error_message("Interrupted in console, exiting...")
            exit(0)

        try:
            t_ex.join(1)
            t_ui.join(1)
        except Exception:
            pass

    def handle_session(
        self,
        type: SessionEventType,
        msg: str,
        extra: Any,
        session_id: str,
        **kwargs: Any,
    ):
        pass

    def handle_round(
        self,
        type: RoundEventType,
        msg: str,
        extra: Any,
        round_id: str,
        session_id: str,
        **kwargs: Any,
    ):
        pass

    def handle_post(
        self,
        type: PostEventType,
        msg: str,
        extra: Any,
        post_id: str,
        round_id: str,
        session_id: str,
        **kwargs: Any,
    ):
        pass


def chat_taskweaver(app_dir: Optional[str] = None):
    TaskWeaverChatApp(app_dir=app_dir).run()


if __name__ == "__main__":
    chat_taskweaver()
