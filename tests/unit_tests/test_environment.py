import glob
import json
import os
import shutil
from typing import Optional

import pytest
from jupyter_client import BlockingKernelClient

from taskweaver.ces import Environment, EnvMode

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def connect_and_execute_code(
    connection_file: str,
    ports_file: Optional[str] = None,
):
    # Create the blocking client
    client = BlockingKernelClient()
    client.load_connection_file(connection_file)
    client.ip = "127.0.0.1"

    if ports_file is not None:
        with open(ports_file, "r") as f:
            ports = json.load(f)

        client.shell_port = ports["shell_port"]
        client.iopub_port = ports["iopub_port"]
        client.stdin_port = ports["stdin_port"]
        client.hb_port = ports["hb_port"]
        client.control_port = ports["control_port"]

    client.wait_for_ready(10)
    client.start_channels()

    result_msg_id = client.execute(
        code='open("filename.txt", "w").write("File content goes here.")',
        silent=False,
        store_history=True,
        allow_stdin=False,
        stop_on_error=True,
    )
    try:
        while True:
            message = client.get_iopub_msg(timeout=180)

            assert message["parent_header"]["msg_id"] == result_msg_id
            msg_type = message["msg_type"]
            if msg_type == "status":
                if message["content"]["execution_state"] == "idle":
                    break
            elif msg_type == "stream":
                stream_name = message["content"]["name"]
                stream_text = message["content"]["text"]

                if stream_name == "stdout":
                    print("stdout:", stream_text)
                elif stream_name == "stderr":
                    print("stderr:", stream_text)
                else:
                    assert False, f"Unsupported stream name: {stream_name}"

            elif msg_type == "execute_result":
                execute_result = message["content"]["data"]
                print("execute_result:", execute_result)
            elif msg_type == "error":
                error_name = message["content"]["ename"]
                error_value = message["content"]["evalue"]
                error_traceback_lines = message["content"]["traceback"]
                if error_traceback_lines is None:
                    error_traceback_lines = [f"{error_name}: {error_value}"]
                error_traceback = "\n".join(error_traceback_lines)
                print("error:", error_traceback)
            elif msg_type == "execute_input":
                pass
            elif msg_type == "display_data":
                print("display:", message["content"])
            elif msg_type == "update_display_data":
                print("update_display:", message["content"])
            else:
                pass
    finally:
        client.stop_channels()


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_environment_start_subprocess():
    # get cwd of current file
    cwd = os.path.dirname(os.path.abspath(__file__))
    sessions = os.path.join(cwd, "sessions")
    try:
        env = Environment("local", env_mode=EnvMode.Local)
        env.start_session(
            session_id="session_id",
        )

        assert os.path.isdir(sessions)
        session_dir = os.path.join(sessions, "session_id")
        assert os.path.isdir(session_dir)
        ces_dir = os.path.join(session_dir, "ces")
        assert os.path.isdir(ces_dir)
        file_glob = os.path.join(ces_dir, "conn-session_id-*.json")
        assert len(glob.glob(file_glob)) == 1
        connection_file = glob.glob(file_glob)[0]
        log_file = os.path.join(ces_dir, "kernel_logging.log")
        assert os.path.isfile(log_file)

        connect_and_execute_code(connection_file)

        saved_file = os.path.join(session_dir, "cwd", "filename.txt")
        assert os.path.isfile(saved_file)

        env.stop_session("session_id")
        assert not os.path.isfile(connection_file)
    finally:
        # delete sessions
        shutil.rmtree(sessions)


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_environment_start_outside_container():
    # get cwd of current file
    cwd = os.path.dirname(os.path.abspath(__file__))
    sessions = os.path.join(cwd, "sessions")
    try:
        env = Environment("local", env_mode=EnvMode.OutsideContainer)
        env.start_session(
            session_id="session_id",
        )

        assert os.path.isdir(sessions)
        session_dir = os.path.join(sessions, "session_id")
        assert os.path.isdir(session_dir)
        ces_dir = os.path.join(session_dir, "ces")
        assert os.path.isdir(ces_dir)
        conn_file_glob = os.path.join(ces_dir, "conn-session_id-*.json")
        assert len(glob.glob(conn_file_glob)) == 1
        connection_file = glob.glob(conn_file_glob)[0]
        ports_file = os.path.join(ces_dir, "ports.json")
        assert os.path.isfile(ports_file)
        log_file = os.path.join(ces_dir, "kernel_logging.log")
        assert os.path.isfile(log_file)

        connect_and_execute_code(connection_file, ports_file)

        saved_file = os.path.join(session_dir, "cwd", "filename.txt")
        assert os.path.isfile(saved_file)

        env.stop_session("session_id")
    finally:
        # delete sessions
        shutil.rmtree(sessions)


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
def test_environment_start_inside_container():
    env = Environment("local", env_mode=EnvMode.InsideContainer)

    # get cwd of current file
    cwd = os.path.dirname(os.path.abspath(__file__))
    sessions = os.path.join(cwd, "sessions")
    os.makedirs(sessions, exist_ok=True)

    session_dir = os.path.join(sessions, "session_id")
    os.makedirs(session_dir, exist_ok=True)

    ces_dir = os.path.join(session_dir, "ces")
    cwd_dir = os.path.join(session_dir, "cwd")

    os.makedirs(ces_dir, exist_ok=True)
    os.makedirs(cwd_dir, exist_ok=True)

    try:
        env.start_session(
            session_id="session_id",
            port_start_inside_container=12345,
            kernel_id_inside_container="kernel_id",
        )

        connection_file = os.path.join(ces_dir, "conn-session_id-kernel_id.json")
        assert os.path.isfile(connection_file)

        connect_and_execute_code(connection_file)

        saved_file = os.path.join(cwd_dir, "filename.txt")
        assert os.path.isfile(saved_file)

        env.stop_session("session_id")
        assert not os.path.isfile(connection_file)
    finally:
        # delete sessions
        shutil.rmtree(sessions)
