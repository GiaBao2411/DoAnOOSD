"""Giám sát hệ thống bằng OpenTelemetry (trace).

- Mỗi yêu cầu HTTP tới FastAPI tạo một span; mỗi câu lệnh SQL qua SQLAlchemy tạo span con, nên xem được
  một yêu cầu mất bao lâu ở tầng web và ở CSDL.
- Các sự kiện nghiệp vụ quan trọng (gửi báo cáo, thiết bị đo gửi số liệu, đổi trạng thái) được gắn thêm
  thuộc tính và sự kiện vào span đang chạy bằng hàm danh_dau().
- Chỉ bật khi có biến môi trường OTEL_EXPORTER_OTLP_ENDPOINT (vd http://jaeger:4318 trong docker-compose).
  Không đặt biến này (vd khi chạy kiểm thử) thì hệ thống chạy bình thường, không gửi gì đi.
"""
import logging
import os

log = logging.getLogger("telemetry")

try:  # thư viện OpenTelemetry có trong requirements.txt; thiếu thì bỏ qua để hệ thống vẫn chạy
    from opentelemetry import trace
except ImportError:  # pragma: no cover
    trace = None


def danh_dau(su_kien: str, **thuoc_tinh):
    """Gắn một sự kiện nghiệp vụ vào span của yêu cầu đang xử lý (không làm gì nếu chưa bật giám sát)."""
    if trace is None:
        return
    span = trace.get_current_span()
    if not span or not span.is_recording():
        return
    tt = {"app." + k: (v if isinstance(v, (str, bool, int, float)) else str(v)) for k, v in thuoc_tinh.items() if v is not None}
    span.set_attributes(tt)
    span.add_event(su_kien, tt)


def bat_giam_sat(app, engine) -> bool:
    """Bật OpenTelemetry cho ứng dụng FastAPI và engine SQLAlchemy. Trả về True nếu đã bật."""
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
    # OTLPSpanExporter tự đọc OTEL_EXPORTER_OTLP_ENDPOINT và gửi tới <endpoint>/v1/traces
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    # Bỏ qua tệp tĩnh của giao diện và ảnh bằng chứng cho đỡ nhiễu
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider, excluded_urls="assets/.*,tep/.*,favicon.*",
                                       exclude_spans=["receive", "send"])
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=provider)
    log.warning("OpenTelemetry: đã bật, gửi trace tới %s (dịch vụ %s)", os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"], ten)
    return True
