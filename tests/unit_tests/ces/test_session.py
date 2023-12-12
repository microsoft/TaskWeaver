import dataclasses
from typing import Callable, List, Optional

import pytest

from taskweaver.ces.common import ExecutionResult, Manager


@dataclasses.dataclass
class RoundSpec:
    id: str
    code: str
    expect_success: bool = True
    output: Optional[str] = None
    stdout: Optional[List[str]] = None
    assessment: Optional[Callable[[ExecutionResult], bool]] = None


@dataclasses.dataclass
class SessionSpec:
    id: str
    round_list: List[RoundSpec] = dataclasses.field(default_factory=list)


spec_def = [
    SessionSpec(
        id="simple_session",
        round_list=[
            RoundSpec(
                id="return_str",
                code="'Hello World!'",
                output="Hello World!",
            ),
            RoundSpec(
                id="return_str_as_var",
                code="result = 'Hello World!'",
                output="Hello World!",
            ),
            RoundSpec(
                id="print_str",
                code="print('Hello World!')",
                output="",
                stdout=["Hello World!\n"],
            ),
        ],
    ),
    SessionSpec(
        id="failed_cases",
        round_list=[
            # RoundSpec(
            #     id="syntax_error",
            #     code="Hello World!",
            #     expect_success=False,
            #     assessment=lambda r: r.error is not None and "SyntaxError" in r.error,
            # ),
            RoundSpec(
                id="syntax_error_2",
                code="[1, 2, {",
                expect_success=False,
                assessment=lambda r: r.error is not None and "SyntaxError" in r.error,
            ),
            RoundSpec(
                id="not_defined",
                code="Hell_World",
                # output="Hello World!",
                expect_success=False,
            ),
        ],
    ),
]


@pytest.mark.parametrize(
    "session_spec",
    spec_def,
)
def test_ces_session(ces_manager: Manager, session_spec: SessionSpec):
    session = ces_manager.get_session_client(session_spec.id)

    session.start()
    for round in session_spec.round_list:
        result: ExecutionResult = session.execute_code(round.id, round.code)

        if not result.is_success:
            assert result.error is not None, "Expecting error message to be present"

        assert (
            result.is_success if round.expect_success else not result.is_success
        ), f"Expecting execution to be {'successful' if round.expect_success else 'unsuccessful'}"

        if round.output is not None:
            assert result.output == round.output, "Expecting output to match"

        if round.stdout is not None:
            for line, comp in enumerate(zip(result.stdout, round.stdout)):
                assert comp[0] == comp[1], f"Expecting stdout line {line + 1} to match: {comp[0]} != {comp[1]}"

        if round.assessment is not None:
            round.assessment(result)

    session.stop()
