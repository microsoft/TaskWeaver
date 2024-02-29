from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

resource = Resource(
    attributes={
        SERVICE_NAME: "taskweaver.opentelemetry.tracer",
    },
)

provider = TracerProvider(resource=resource)

otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4318/v1/traces")
processor = BatchSpanProcessor(otlp_exporter)

provider.add_span_processor(processor)

# Sets the global default tracer provider
trace.set_tracer_provider(provider)

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer(__name__)


def get_current_span():
    return trace.get_current_span()
