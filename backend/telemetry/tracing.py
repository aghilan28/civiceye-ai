from __future__ import annotations

from contextvars import ContextVar
from dataclasses import asdict, dataclass
from uuid import uuid4


_trace_context: ContextVar["TraceContext | None"] = ContextVar("civiceye_trace_context", default=None)


@dataclass(frozen=True)
class TraceContext:
    correlation_id: str
    request_id: str
    trace_id: str
    orchestration_trace_id: str | None = None
    worker_trace_id: str | None = None
    inference_trace_id: str | None = None
    tenant_id: str | None = None

    def to_headers(self) -> dict[str, str]:
        headers = {
            "X-CivicEye-Correlation-Id": self.correlation_id,
            "X-CivicEye-Request-Id": self.request_id,
            "X-CivicEye-Trace-Id": self.trace_id,
        }
        if self.orchestration_trace_id:
            headers["X-CivicEye-Orchestration-Trace-Id"] = self.orchestration_trace_id
        if self.worker_trace_id:
            headers["X-CivicEye-Worker-Trace-Id"] = self.worker_trace_id
        if self.inference_trace_id:
            headers["X-CivicEye-Inference-Trace-Id"] = self.inference_trace_id
        return headers

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def new_trace_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


def make_trace_context(
    *,
    correlation_id: str | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
    tenant_id: str | None = None,
) -> TraceContext:
    base = trace_id or new_trace_id("trace")
    return TraceContext(
        correlation_id=correlation_id or new_trace_id("corr"),
        request_id=request_id or new_trace_id("req"),
        trace_id=base,
        orchestration_trace_id=new_trace_id("orch"),
        worker_trace_id=new_trace_id("worker"),
        inference_trace_id=new_trace_id("infer"),
        tenant_id=tenant_id,
    )


def set_trace_context(context: TraceContext) -> None:
    _trace_context.set(context)


def current_trace_context() -> TraceContext:
    context = _trace_context.get()
    if context is None:
        context = make_trace_context()
        set_trace_context(context)
    return context


def trace_from_headers(headers, *, tenant_id: str | None = None) -> TraceContext:
    get = headers.get
    context = TraceContext(
        correlation_id=get("x-civiceye-correlation-id") or get("X-CivicEye-Correlation-Id") or new_trace_id("corr"),
        request_id=get("x-civiceye-request-id") or get("X-CivicEye-Request-Id") or new_trace_id("req"),
        trace_id=get("x-civiceye-trace-id") or get("X-CivicEye-Trace-Id") or new_trace_id("trace"),
        orchestration_trace_id=get("x-civiceye-orchestration-trace-id") or get("X-CivicEye-Orchestration-Trace-Id"),
        worker_trace_id=get("x-civiceye-worker-trace-id") or get("X-CivicEye-Worker-Trace-Id"),
        inference_trace_id=get("x-civiceye-inference-trace-id") or get("X-CivicEye-Inference-Trace-Id"),
        tenant_id=tenant_id,
    )
    set_trace_context(context)
    return context


def enrich_payload(payload: dict, **extra) -> dict:
    context = current_trace_context().to_dict()
    return {**payload, "trace": {**context, **extra}}
