import threading
import time
from typing import List, Optional

import click
from colorama import ansi

from taskweaver.app.app import TaskWeaverApp


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


def user_input_message(prompt: str = "Human"):
    import os

    import prompt_toolkit
    import prompt_toolkit.history

    history = prompt_toolkit.history.FileHistory(os.path.expanduser("~/.taskweaver-history"))
    session = prompt_toolkit.PromptSession(
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


def chat_taskweaver(app_dir: Optional[str] = None):
    app = TaskWeaverApp(app_dir=app_dir, use_local_uri=True)
    session = app.get_session()

    # prepare data file
    assistant_message(
        "I am TaskWeaver, an AI assistant. To get started, could you please enter your request?",
    )

    while True:
        user_query = user_input_message()
        if user_query == "":
            error_message("Empty input, please try again")
            continue

        lock = threading.Lock()
        messages: List = []
        response = []

        def execution_thread():
            def event_handler(type: str, msg: str):
                with lock:
                    messages.append((type, msg))

            event_handler("stage", "starting")
            try:
                response.append(
                    session.send_message(
                        user_query,
                        event_handler=event_handler,
                    ),
                )
            except Exception as e:
                response.append("Error")
                raise e

        def ani_thread():
            counter = 0
            stage = "preparing"

            def clear_line():
                print(ansi.clear_line(), end="\r")

            def process_messages(stage):
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

        t_ex.join()
        t_ui.join()


if __name__ == "__main__":
    chat_taskweaver()
