from typing import Any, Dict, Optional

from taskweaver.ces.common import Manager


def test_user_input(ces_manager: Manager) -> None:
    session = ces_manager.get_session_client("test_session")

    session.start()
    input_prompt = "Enter something: "
    input_result = "Hello World!"

    def on_event(event_type: str, event_data: str, extra: Optional[Dict[str, Any]]) -> Optional[str]:
        if event_type == "input":
            assert event_data == input_prompt
            return input_result
        return None

    result = session.execute_code(
        "test",
        f"input('{input_prompt}')",
        allow_input=True,
        on_event=on_event,
    )
    assert result.output == input_result
