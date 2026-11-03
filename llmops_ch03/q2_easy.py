# -*- coding: utf-8 -*-
# 3장 2강 퀴즈: 문맥을 늘리자는 제안을 같은 질문으로 재 봐요 (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q2_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
import re
from quiz_lab import setup
from course import DOCUMENTS, answer

ALL_DOCS = "\n" + "\n".join(f"[{d['id']}] {d['text']}" for d in DOCUMENTS)
QUESTIONS = ["식비 한도와 필요한 서류는 무엇인가요?", "재택근무 지원금은 얼마인가요?"]


# 상황: '일단 전체 규정을 다 넣자'는 제안이 왔어요. 규정 밖 질문도 함께 재요.
def main(lf, model, questions):
    rows = []
    for index, question in enumerate(questions):
        for version in ("narrow", "all_docs"):
            padding = ALL_DOCS if version == "all_docs" else ""
            row = answer(lf, model, question,
                         extra_context=padding, version=version)
            row["case_id"] = f"q{index + 1}"
            rows.append(row)
    return rows


def cites(row):
    return set(re.findall(r"\[(\w+)\]", row["answer"]))


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
lf, model = setup()
rows = main(lf, model, QUESTIONS)
assert len(rows) == 4, "질문 2개 × 두 버전, 네 행이어야 해요"
table = {(r["case_id"], r["app_version"]): r for r in rows}
assert set(table) == {(c, v) for c in ("q1", "q2") for v in ("narrow", "all_docs")}, "case_id와 version을 확인하세요"
for key in sorted(table):
    r = table[key]
    print(f'{key[0]} {key[1]:<9} 입력 토큰(설명용)={r["usage"]["input_tokens"]:<4} 검색={r["document_ids"]} 답변 출처={sorted(cites(r))}')
for case in ("q1", "q2"):
    assert table[case, "all_docs"]["usage"]["input_tokens"] > table[case, "narrow"]["usage"]["input_tokens"], "전체 규정을 넣으면 입력이 늘어요"
assert cites(table["q1", "narrow"]) == {"meal"}
assert cites(table["q1", "all_docs"]) == {"meal", "travel", "training"}, "관계없는 규정까지 출처로 붙었어요"
assert cites(table["q2", "narrow"]) == set() and "확인할 수 없습니다" in table["q2", "narrow"]["answer"], "규정 밖 질문은 보류해요"
assert cites(table["q2", "all_docs"]) and table["q2", "all_docs"]["document_ids"] == [], "검색은 비었는데 답변에는 출처가 있어요"
print("document_ids만 보면 q2 all_docs는 여전히 빈 목록이에요. 답변 문장까지 읽어야 해요.")
print("\n✅ 정답이에요!")
print("생각해 보기:", "이 답은 규칙 모델의 결과라 실제 모델은 더 잘 고를 수도 있어요. 그래도 비용이 늘어난 만큼 무엇이 좋아져야 이 제안을 받아들일 수 있을까요? 궁금하면 02_measure.py의 padding을 바꿔 실제 모델로 재 보세요(모델 호출 비용이 있어요).")
