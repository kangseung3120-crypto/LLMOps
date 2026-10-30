# -*- coding: utf-8 -*-
# 1장 1강 퀴즈: 수료증은 어느 단계에서 사라졌을까요? (정답 코드예요)
# 이 폴더에서 uv run q1_solution.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

from course import retrieve

REQUIRED = ["영수증", "수료증"]


def build_context(question):
    # course.py의 answer()와 같은 방식으로 검색 문서를 "[id] 본문" 형태로 묶어요.
    return "\n".join(f"[{d['id']}] {d['text']}" for d in retrieve(question))


# 교육비 답변에서 수료증이 빠졌어요. 앞 단계의 증거부터 확인해 실패가 처음 드러난 위치를 반환하세요.
def locate(question, context, answer):
    if not retrieve(question):  # 검색 문서가 하나도 없어요
        return "검색"
    if not all(term in context for term in REQUIRED):
        return "입력 조립"
    if not all(term in answer for term in REQUIRED):
        return "생성"
    return "정상"


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
q = "교육비 증빙 서류는 무엇인가요?"
full = build_context(q)
cases = [
    ("A", "자기계발 지원을 받으려면 뭘 내나요?", "", "확인할 수 없습니다."),
    ("B", q, "[training] 교육비는 연간 20만원까지 지원하며 영수증이 필요합니다.", "영수증이 필요합니다. [training]"),
    ("C", q, full, "교육비는 영수증이 필요합니다. [training]"),
    ("D", q, full, "영수증과 수료증이 필요합니다. [training]"),
]
results = {}
for name, question, context, answer in cases:
    results[name] = locate(question, context, answer)
    print(f"{name}: {results[name]:<6} | 질문: {question} | 답변: {answer}")
assert results["A"] == "검색", "A는 키워드가 없어 검색 문서가 비어요"
assert results["B"] == "입력 조립", "B는 training을 찾았지만 모델 입력에 수료증 문장이 없어요"
assert results["C"] == "생성", "C는 입력에 두 증빙이 있는데 답변에서 수료증이 빠졌어요"
assert results["D"] == "정상", "D는 두 증빙이 모두 답변에 있어요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "A처럼 검색이 비었고 모델이 '확인할 수 없습니다'라고 답했다면 실패일까요? 규정 밖 질문인지, 표현 차이로 못 찾은 것인지 어떻게 구분할까요?")
