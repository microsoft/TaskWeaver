import pytest


@pytest.fixture()
def ces_manager(tmp_path: str):
    from taskweaver.ces import code_execution_service_factory

    return code_execution_service_factory(tmp_path)
