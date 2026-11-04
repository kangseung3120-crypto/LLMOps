# -*- coding: utf-8 -*-
# 4장 3강 퀴즈: 사람 확인 상태를 추가하면 계약은 어떻게 바뀔까요? (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q3_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드 answer()와 Answer를 그대로 써요. 답변만 정해진 문자열로 바꿔요.
import json
from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import model_validator
from course import answer
from guards import Answer
from quiz_lab import FakeLf, RuleModel


class Scripted(RuleModel):
    """정해 둔 문자열을 그대로 답하는 가짜 모델이에요."""
    reply: str = ""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        message = AIMessage(content=self.reply, response_metadata={"status": "completed"})
        return ChatResult(generations=[ChatGeneration(message=message)])


class ReviewAnswer(Answer):
    # 상태가 하나 늘었어요. extra="forbid", strict=True와 수업의 관계 검사는 그대로 물려받아요.
    status: Literal["answered", "abstained", "needs_review"]
    reason: str | None = None

# 상황: 새 상태 needs_review에만 reason이 있어요.
    @model_validator(mode="after")
    def check_review(self):
        if self.status == "needs_review" and not self.reason:
            raise ValueError("사람 확인에는 이유가 필요해요.")
        if self.status != "needs_review" and self.reason:
            raise ValueError("이 상태에는 이유를 붙이지 않아요.")
        return self

def route(text, allowed_ids):
    try:
        parsed = ReviewAnswer.model_validate_json(text)
    except ValueError:
        return "REJECT:형식"
    if not set(parsed.citations) <= set(allowed_ids):
        return "REJECT:출처"
    return "HUMAN" if parsed.status == "needs_review" else "SEND"


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
def js(**fields):
    return json.dumps(fields, ensure_ascii=False)


OK = "교육비는 연간 20만원까지 지원해요."
cases = [
    ("정상 답변", js(status="answered", answer=OK, citations=["training"]), "SEND"),
    ("보류", js(status="abstained", answer="확인할 수 없습니다.", citations=[]), "SEND"),
    ("사람 확인", js(status="needs_review", answer=OK, citations=["training"], reason="규정 개정 중"), "HUMAN"),
    ("이유 없는 사람 확인", js(status="needs_review", answer=OK, citations=["training"]), "REJECT:형식"),
    ("보류에 이유", js(status="abstained", answer="확인할 수 없습니다.", citations=[], reason="없음"), "REJECT:형식"),
    ("출처 없는 답변", js(status="answered", answer=OK, citations=[]), "REJECT:형식"),
    ("JSON 뒤에 설명", js(status="answered", answer=OK, citations=["training"]) + " 도움이 됐나요?", "REJECT:형식"),
    ("예상 밖 필드", js(status="answered", answer=OK, citations=["training"], score=1), "REJECT:형식"),
    ("존재하지만 검색 안 된 출처", js(status="answered", answer=OK, citations=["meal"]), "REJECT:출처"),
    ("사람 확인도 출처 범위 검사", js(status="needs_review", answer=OK, citations=["secret"], reason="확인"), "REJECT:출처"),
]
lf = FakeLf()
for label, reply, want in cases:
    # 진짜 answer()가 돌려준 답변과 이번 요청의 document_ids를 그대로 검사해요.
    row = answer(lf, Scripted(reply=reply), "교육비 한도와 증빙 서류는 무엇인가요?")
    got = route(row["answer"], row["document_ids"])
    print(f"{label:<16} 검색 {row['document_ids']} -> {got}")
    assert got == want, f"{label}: {want}여야 해요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "needs_review라도 출처 범위를 검사해야 할까요? 정답처럼 보이지만 금액이 틀린 답변은 어느 경로로 갈까요? HUMAN으로 가는 비율이 늘면 어떤 운영 지표(3장)를 함께 봐야 할까요?")
