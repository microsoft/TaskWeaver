from typing import Any, Dict, Literal, Optional

from injector import inject

from taskweaver.config.module_config import ModuleConfig


class TracingConfig(ModuleConfig):
    def _configure(self):
        self._set_name("tracing")
        self.enabled = self._get_bool("enabled", False)
        self.endpoint = self._get_str("endpoint", "http://127.0.0.1:4317")
        self.service_name = self._get_str("service_name", "taskweaver.otlp.tracer")
        self.exporter = self._get_str("exporter", "otlp")
        self.tokenizer_target_model = self._get_str("tokenizer_target_model", "gpt-4")


_tracer = None
_trace = None
_StatusCode = None
_meter = None
_counters: Dict[str, Any] = {}
_enc = None


class Tracing:
    @inject
    def __init__(
        self,
        config: TracingConfig,
    ):
        global _tracer, _trace, _StatusCode, _meter, _enc, _counters

        self.config = config
        if not self.config.enabled:
            return

        if _tracer is not None:
            return

        try:
            import tiktoken
            from opentelemetry import metrics, trace
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
            from opentelemetry.trace import StatusCode

        except ImportError:
            raise ImportError(
                "Please install opentelemetry-sdk, "
                "opentelemetry-api, "
                "opentelemetry-exporter-otlp, "
                "opentelemetry-instrumentation, "
                "tiktoken "
                "first.",
            )

        resource = Resource(
            attributes={
                SERVICE_NAME: self.config.service_name,
            },
        )

        trace_provider = TracerProvider(resource=resource)

        if self.config.exporter == "otlp":
            trace_exporter = OTLPSpanExporter(endpoint=self.config.endpoint)
            metrics_exporter = OTLPMetricExporter(endpoint=self.config.endpoint)
        elif self.config.exporter == "console":
            trace_exporter = ConsoleSpanExporter()
            metrics_exporter = ConsoleMetricExporter()
        else:
            raise ValueError(f"Unknown exporter: {self.config.exporter}")

        processor = BatchSpanProcessor(trace_exporter)
        trace_provider.add_span_processor(processor)

        # Sets the global default tracer provider
        trace.set_tracer_provider(trace_provider)

        _tracer = trace.get_tracer(__name__)
        _trace = trace
        _StatusCode = StatusCode

        metric_reader = PeriodicExportingMetricReader(metrics_exporter)
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        _meter = metrics.get_meter(__name__)
        _counters["prompt_size"] = _meter.create_counter(
            "prompt_size",
            unit="1",
            description="Counts the number of tokens in the prompt.",
        )
        # To get the tokeniser corresponding to a specific model in the OpenAI API:
        _enc = tiktoken.encoding_for_model(self.config.tokenizer_target_model)

    @staticmethod
    def set_span_status(
        status_code: Literal["OK", "ERROR"],
        status_message: Optional[str] = None,
    ):
        if _trace is None:
            return

        span = _trace.get_current_span()
        status_code = _StatusCode.OK if status_code == "OK" else _StatusCode.ERROR
        if status_code == _StatusCode.OK:
            status_message = None
        span.set_status(status_code, status_message)

    @staticmethod
    def set_span_attribute(key, value):
        if _trace is None:
            return

        span = _trace.get_current_span()
        span.set_attribute(key, value)

    @staticmethod
    def set_span_exception(exception):
        if _trace is None:
            return

        span = _trace.get_current_span()
        span.record_exception(exception)

    @staticmethod
    def add_prompt_size(size: int = 0, labels: Optional[Dict[str, str]] = None):
        if _meter is None:
            return

        _counters["prompt_size"].add(
            size,
            labels or {},
        )

    @staticmethod
    def count_tokens(data: str) -> int:
        if _enc is None:
            return 0

        return len(_enc.encode(data))


class DummyTracer:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def start_as_current_span(self, span_name):
        return self

    def set_attribute(self, key, value):
        pass

    def set_status(self, status_code, status_message: Optional[str] = None):
        pass

    def record_exception(self, exception):
        pass


def tracing_decorator_non_class(func):
    def wrapper(*args, **kwargs):
        if _tracer is None:
            return func(*args, **kwargs)

        with _tracer.start_as_current_span(func.__name__):
            result = func(*args, **kwargs)
        return result

    return wrapper


def tracing_decorator(func):
    def wrapper(self, *args, **kwargs):
        if _tracer is None:
            return func(self, *args, **kwargs)

        span_name = f"{self.__class__.__name__}.{func.__name__}"
        with _tracer.start_as_current_span(span_name):
            result = func(self, *args, **kwargs)
        return result

    return wrapper


def get_tracer():
    if _tracer is None:
        return DummyTracer()

    return _tracer
