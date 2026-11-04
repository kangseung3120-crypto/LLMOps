# -*- coding: utf-8 -*-
# 4장 2강 퀴즈: 이메일 말고 휴대폰 번호까지 들어오면? (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q2_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드 answer(), redact(), mask_spans()를 규칙 모델(가짜)로 돌려요. 번호와 메일은 모두 가상이에요.
import re
from types import SimpleNamespace
import guards
from quiz_lab import FakeLf, RuleModel
from course import answer

email_only = guards.redact


class Spy(RuleModel):
    """모델에 실제로 전달된 메시지를 모아 둬요."""
    seen: list = []

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.seen.extend(m.content for m in messages)
        return super()._generate(messages, stop, run_manager, **kwargs)


# 상황: 학생이 휴대폰 번호까지 함께 적기 시작했어요. 번호도 가리고, 모델 답변에서도 찾아내세요.
def redact_all(text):
    # 하이픈이 있어도 없어도 찾아요. 2026-01-01 같은 날짜와 200000원은 그대로 둬요.
    return re.sub(r"01[016789]-?\d{3,4}-?\d{4}", "[PHONE]", email_only(text))


def ask(lf, model, original, extra_context=""):
    row = answer(lf, model, redact_all(original), extra_context=extra_context)
    if redact_all(row["answer"]) != row["answer"]:
        raise RuntimeError("PII_IN_OUTPUT")
    return row


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
EMAIL, PHONE = "demo.student@example.com", "010-1234-5678"
for text, want in [
    (f"{PHONE}이고 식비는?", "[PHONE]이고 식비는?"),
    ("01012345678로 연락 주세요", "[PHONE]로 연락 주세요"),
    (f"{EMAIL}의 식비 한도", "[EMAIL]의 식비 한도"),
    ("2026-01-01부터 200000원 지원", "2026-01-01부터 200000원 지원"),
    ("문서 번호 1234567890 확인", "문서 번호 1234567890 확인"),
]:
    got = redact_all(text)
    print(f"{text} -> {got}")
    assert got == want, f"{text}는 {want}가 돼야 해요"

# 1) 모델이 받은 메시지에 원문이 없어야 해요.
lf = FakeLf()
model = Spy(lf=lf, seen=[])
row = ask(lf, model, f"{EMAIL}, {PHONE}입니다. 식비 한도와 필요한 서류는 무엇인가요?")
print("모델이 받은 질문:", row["question"])
print("답변:", row["answer"])
assert not any(EMAIL in m or PHONE in m for m in model.seen), "원문을 모델에 보내면 안 돼요"
assert "2만원" in row["answer"] and "영수증" in row["answer"], "가려도 업무 답변은 유지돼요"

# 2) 입력에 없던 번호가 답변에 나오면 표시 전에 멈춰야 해요. 원문 비교만으로는 못 잡아요.
for value in ("010-2222-3333", "staff.demo@example.com"):
    leak = None
    try:
        ask(lf, Spy(lf=lf, seen=[]), "식비 한도는?", extra_context=f"\n[contact] 담당자 연락처는 {value}입니다.")
    except RuntimeError as exc:
        leak = str(exc)
    print("문서의 연락처가 답변에 나옴:", leak)
    assert leak == "PII_IN_OUTPUT", "답변에 번호나 메일이 있으면 PII_IN_OUTPUT이어야 해요"

# 3) 진짜 mask_spans도 같은 필터를 쓰면 관측 속성까지 바뀌어요. 문자열 속성만 다뤄요.
guards.redact = redact_all
spans = {"s1": SimpleNamespace(attributes={"input": PHONE, "safe": "식비", "count": 3})}
patch = guards.mask_spans(params=SimpleNamespace(spans=spans)).span_patches["s1"].set_attributes
print("관측 속성 변경:", patch)
assert patch == {"input": "[PHONE]"}, "달라진 문자열 속성만 바꿔요"
guards.redact = email_only

# 4) 정규식의 한계도 확인해요.
assert redact_all("학생 골뱅이 회사 점 com") == "학생 골뱅이 회사 점 com"
print("변형 표기 그대로:", redact_all("학생 골뱅이 회사 점 com"))
print("\n✅ 정답이에요!")
print("생각해 보기:", "수업 코드의 출력 검사는 원문 문자열만 비교했어요. 이번 검사와 무엇이 다른가요? 업무상 담당자 번호를 꼭 안내해야 하는 서비스라면 이 검사를 어떻게 바꿔야 할까요? 이름을 가리려면 정규식 말고 무엇이 필요할까요?")
