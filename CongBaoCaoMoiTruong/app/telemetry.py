import logging
import os

log = logging.getLogger("telemetry")

try:
    from opentelemetry import trace
except ImportError:
    trace = None


def danh_dau(su_kien: str, **thuoc_tinh):
    if trace is None:
        return
    span = trace.get_current_span()
    if not span or not span.is_recording():
        return
    tt = {"app." + k: (v if isinstance(v, (str, bool, int, float)) else str(v)) for k, v in thuoc_tinh.items() if v is not None}
    span.set_attributes(tt)
    span.add_event(su_kien, tt)


def bat_giam_sat(app, engine) -> bool:
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or trace is None:
        return False
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    ten = os.environ.get("OTEL_SERVICE_NAME", "cong-bao-cao-moi-truong")
    provider = TracerProvider(resource=Resource.create({"service.name": ten, "service.version": "2.0"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider, excluded_urls="assets/.*,tep/.*,favicon.*",
                                       exclude_spans=["receive", "send"])
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=provider)
    log.warning("OpenTelemetry: đã bật, gửi trace tới %s (dịch vụ %s)", os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"], ten)
    return True
