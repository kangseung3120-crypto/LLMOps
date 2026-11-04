"""모델의 지시와 관계없이 애플리케이션이 검사해야 하는 경계예요."""

import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from langfuse.types import MaskOtelSpansResult, OtelSpanPatch


def redact(text):
    # 수업에서는 이메일 형태만 다뤄요. 이름, 주소, 변형된 개인정보까지 탐지하는 완성품은 아니에요.
    return re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)


def mask_spans(*, params):
    # Langfuse로 보내는 문자열 속성에 같은 이메일 필터를 적용해요.
    # 입력 사전 처리와 별개로 관측 데이터의 출력에도 보호를 덧대는 단계예요.
    # params.spans는 내보낼 span들의 모음이에요. 식별자별 변경 속성만 반환하면 SDK가 적용해요.
    patches = {}
    for identifier, span in params.spans.items():
        # 문자열 속성에만 이메일 치환을 적용해요. 이름, 이벤트와 다른 exporter까지 보호하지는 않아요.
        changed = {
            key: redact(value)
            for key, value in span.attributes.items()
            if isinstance(value, str) and redact(value) != value
        }
        if changed:
            patches[identifier] = OtelSpanPatch(set_attributes=changed)
    return MaskOtelSpansResult(span_patches=patches)


class Answer(BaseModel):
    # 문자열 JSON이라는 사실과 서비스가 사용할 수 있는 답변이라는 사실은 달라요.
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["answered", "abstained"]
    answer: str = Field(min_length=1, max_length=500)
    citations: list[str]

    # 각 필드가 유효해도 서로 모순될 수 있어요. 파싱 후 관계 규칙을 한 번 더 검사해요.
    @model_validator(mode="after")
    def check_relation(self):
        if not self.answer.strip():
            raise ValueError("답변 본문이 비어 있어요.")
        if self.status == "answered" and not self.citations:
            raise ValueError("답변에는 출처가 필요해요.")
        if self.status == "abstained" and self.citations:
            raise ValueError("보류 답변에는 출처를 붙이지 않아요.")
        return self


CATALOG = {
    "meal": {"tenant": "campus", "text": "식비는 하루 2만원까지 지원합니다."},
    "secret": {"tenant": "other", "text": "OTHER_TENANT_DEMO_SECRET"},
}


def read_document(doc_id, principal, read_ids):
    # principal은 사용자 본문에서 읽으면 안 돼요. 여기서는 인증 결과를 대신하는 고정 객체예요.
    if doc_id not in CATALOG or CATALOG[doc_id]["tenant"] != principal["tenant"]:
        raise PermissionError("DOCUMENT_ACCESS_DENIED")
    # 권한 검사에서 예외가 발생하면 이 줄에 도달하지 않아요. 실제 읽은 목록의 증거예요.
    read_ids.append(doc_id)
    return CATALOG[doc_id]["text"]


def run_tool(proposal, principal, read_ids):
    # 모델은 도구 실행을 제안할 뿐이에요. 이름, 인자, 권한을 검사한 뒤 읽기 도구만 실행해요.
    if (
        not isinstance(proposal, dict)
        or set(proposal) != {"name", "doc_id"}
        or proposal["name"] != "read_document"
        or not isinstance(proposal["doc_id"], str)
    ):
        raise PermissionError("TOOL_NOT_ALLOWED")
    return read_document(proposal["doc_id"], principal, read_ids)
