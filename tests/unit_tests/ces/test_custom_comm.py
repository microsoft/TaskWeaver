from textwrap import dedent

from taskweaver.ces.common import Manager


def test_unsupported_comm(ces_manager: Manager) -> None:
    """
    ipython_widget has custom widget comm, which is not supported.
    But the kernel should properly handle the customized message.
    """

    session = ces_manager.get_session_client("test_session")

    session.start()

    # sample code to display progress with tqdm
    sample_code = dedent(
        """
        from tqdm.notebook import tqdm
        import time

        for i in tqdm(range(2)):
            time.sleep(0.01)
        """,
    )

    session.execute_code(
        "test",
        sample_code,
    )
