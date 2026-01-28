import pytest


@pytest.fixture()
def ces_manager(tmp_path: str):
    """Create a real CES manager for integration tests.

    Note: This fixture creates actual Jupyter kernels and should only be used
    in integration tests, not unit tests. Tests using this fixture may hang
    if the execution environment is not properly configured.
    """
    from taskweaver.ces import code_execution_service_factory

    return code_execution_service_factory(tmp_path)
