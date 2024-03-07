from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource


def test_tracing_disabled():
    app_injector = Injector()
    app_config = AppConfigSource(
        config={
            "tracing.enabled": False,
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    from taskweaver.module.tracing import Tracing, get_tracer, tracing_decorator, tracing_decorator_non_class

    tracing = app_injector.get(Tracing)

    tracing.set_span_attribute("code", "print('Hello, World!')")
    tracing.set_span_status("OK")
    tracing.set_span_status("ERROR", "Code execution failed.")
    tracing.set_span_exception(Exception("Test exception"))

    with get_tracer().start_as_current_span("test_tracing") as span:
        span.set_attribute("test", "test")
        span.set_status("OK")
        span.record_exception(Exception("Test exception"))

    class TestClass:
        @tracing_decorator
        def test_method(self):
            pass

    test_class = TestClass()
    test_class.test_method()

    @tracing_decorator_non_class
    def test_function():
        pass

    test_function()


def test_tracing_enabled():
    app_injector = Injector()
    app_config = AppConfigSource(
        config={
            "tracing.enabled": True,
            "tracing.exporter": "console",
        },
    )
    app_injector.binder.bind(AppConfigSource, to=app_config)
    from taskweaver.module.tracing import Tracing, get_tracer, tracing_decorator, tracing_decorator_non_class

    tracing = app_injector.get(Tracing)

    tracing.set_span_attribute("code", "print('Hello, World!')")
    tracing.set_span_status("OK")
    tracing.set_span_status("ERROR", "Code execution failed.")
    tracing.set_span_exception(Exception("Test exception"))

    with get_tracer().start_as_current_span("test_tracing") as span:
        span.set_attribute("test", "test")
        span.set_status("OK")
        span.record_exception(Exception("Test exception"))

    class TestClass:
        @tracing_decorator
        def test_method(self):
            pass

    test_class = TestClass()
    test_class.test_method()

    @tracing_decorator_non_class
    def test_function():
        pass

    test_function()

    import time

    time.sleep(5)
