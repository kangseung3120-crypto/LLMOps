# -*- coding: utf-8 -*-
# 2장 1강 퀴즈: 새 규정이 생긴 상황으로 데이터셋을 다시 등록해요 (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q1_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
from quiz_lab import lesson, quiet, setup
from course import DOCUMENTS, answer, read
from evaluation import evaluate


# 상황: 경조사비 규정이 새로 생겼어요. 규정과 평가 질문을 함께 추가해요.
NEW_DOC = {"id": "family", "keywords": ["경조사"],
           "text": "경조사비는 1회 10만원까지 지원합니다."}
NEW_ROWS = [
    {"id": "d05", "split": "dev", "kind": "normal",
     "question": "경조사비 한도는 얼마인가요?",
     "expected": {"terms": [____], "citations": [____],
                  "abstain": False}},
    # 규정에 금액만 있고 휴가 일수는 없어요. 확인용으로 처음 평가해요.
    {"id": "t03", "split": ____, "kind": "unanswerable",
     "question": "경조사 휴가는 며칠인가요?",
     "expected": ____},
]


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
module = lesson("01_dataset")
rows = read("golden.json") + NEW_ROWS
terms = NEW_ROWS[0]["expected"]["terms"]
assert all(isinstance(t, str) and t in NEW_DOC["text"] for t in terms), "필수 표현은 규정 문장에 있는 표현이어야 해요. 출처 ID가 아니에요"
# 1) 규정을 추가하기 전에는 없는 출처라서 등록 전에 막혀요.
try:
    module.validate(rows)
    raise AssertionError("family 문서가 없는데 통과했어요. d05의 citations를 확인하세요.")
except ValueError as exc:
    print("규정 추가 전 validate:", exc)
DOCUMENTS.append(NEW_DOC)

# 2) 진짜 01_dataset.py의 main()을 가짜 Langfuse로 실행해요.
lf, model = setup()
saved = {}
module.read = lambda name: rows
module.connect = lambda: (lf, model)
module.save = lambda name, value: saved.update(value)
quiet(module.main)
sizes = {s: len(lf.get_dataset(saved["datasets"][s]).items) for s in ("dev", "holdout")}
print("등록된 항목:", sizes)
assert sizes == {"dev": 5, "holdout": 3}, "dev 5개, holdout 3개가 되어야 해요"

# 3) 진짜 answer()와 evaluate()로 채점해요. 답변은 규칙 모델의 설명용 답이에요.
results = {}
for row in NEW_ROWS:
    reply = answer(lf, model, row["question"])
    scores = {e.name: e.value for e in evaluate(output=reply, expected_output=row["expected"])}
    results[row["id"]] = scores["rule_pass"]
    print(f'{row["id"]} 검색={reply["document_ids"]} rule_pass={scores["rule_pass"]} | {reply["answer"]}')
assert results == {"d05": 1, "t03": 0}, "d05는 통과하고, t03은 기대값에 걸려야 해요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "t03의 키워드 검색은 성공했는데 답할 근거는 없어요. 프롬프트와 검색 중 어디를 고쳐야 할까요? 규칙 모델 대신 실제 모델이라면 어떻게 답할지 예상하고, golden.json에 넣어 03을 돌려 보세요(모델 호출 비용이 있어요).")
