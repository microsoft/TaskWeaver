from typing import Literal, Optional

from injector import inject

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import Span, TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import StatusCode
except ImportError:
    raise ImportError("Please install opentelemetry-sdk first.")

from taskweaver.config.module_config import ModuleConfig


class TracingConfig(ModuleConfig):
    def _configure(self):
        self._set_name("tracing")
        self.enabled = self._get_bool("enabled", True)
        self.endpoint = self._get_str("endpoint", "http://127.0.0.1:4318/v1/traces")
        self.service_name = self._get_str("service_name", "taskweaver.opentelemetry.tracer")


_tracer: trace.Tracer = None


class Tracing:
    @inject
    def __init__(
        self,
        config: TracingConfig,
    ):
        global _tracer

        if _tracer is not None:
            return

        self.config = config

        resource = Resource(
            attributes={
                SERVICE_NAME: self.config.service_name,
            },
        )

        _provider = TracerProvider(resource=resource)

        if self.config.enabled:
            otlp_exporter = OTLPSpanExporter(endpoint=self.config.endpoint)
            processor = BatchSpanProcessor(otlp_exporter)
            _provider.add_span_processor(processor)

        # Sets the global default tracer provider
        trace.set_tracer_provider(_provider)

        _tracer = trace.get_tracer(__name__)
        self.trace = trace


def tracing_decorator_non_class(func):
    def wrapper(*args, **kwargs):
        with _tracer.start_as_current_span(func.__name__):
            result = func(*args, **kwargs)
        return result

    return wrapper


def tracing_decorator(func):
    def wrapper(self, *args, **kwargs):
        span_name = f"{self.__class__.__name__}.{func.__name__}"
        with _tracer.start_as_current_span(span_name):
            result = func(self, *args, **kwargs)
        return result

    return wrapper


def get_tracer():
    return _tracer


def get_current_span():
    return trace.get_current_span()


def set_span_status(
    span: Span,
    status_code: Literal["OK", "ERROR"],
    status_message: Optional[str] = None,
):
    status_code = StatusCode.OK if status_code == "OK" else StatusCode.ERROR
    span.set_status(status_code, status_message)
