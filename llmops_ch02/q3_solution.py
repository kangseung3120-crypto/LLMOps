# -*- coding: utf-8 -*-
# 2장 3강 퀴즈: 실패한 행이 조용히 사라지는 상황을 잡아요 (정답 코드예요)
# 이 폴더에서 uv run q3_solution.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
from types import SimpleNamespace
from quiz_lab import dataset_from, setup
from course import POLICY, read
from evaluation import experiment

DEV = [r for r in read("golden.json") if r["split"] == "dev"]
PROMPT = SimpleNamespace(name="quiz", version=2, prompt=POLICY)


# 상황: 모델이 일부 질문에서 실패해요. SDK는 실패한 Task의 행을 결과에서 빼요.
def main(lf, model, dataset, prompt):
    report = experiment(lf, model, dataset, prompt, "candidate")
    expected_ids = {item.input["id"] for item in dataset.items}
    got_ids = {r["id"] for r in report["rows"]}
    missing = expected_ids - got_ids
    errors = sorted(r["id"] for r in report["rows"] if r["error"])
    if missing or errors:
        return {"status": "EXPERIMENT_HAS_ERRORS",
                "missing": sorted(missing), "errors": errors}
    return {"status": "완료", "rows": report["rows"]}


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
broken = [{**r, "expected": {}} if r["id"] == "d04" else r for r in DEV]  # 평가기가 실패하는 기대값
cases = [
    ("모두 정상", {}, DEV, None, None),
    ("d02 API 오류", {"fail_on": ("숙박",)}, DEV, ["d02"], []),
    ("d03 응답 잘림", {"incomplete_on": ("교육",)}, DEV, ["d03"], []),
    ("d04 평가기 실패", {}, broken, [], ["d04"]),
]
for label, options, rows, missing, errors in cases:
    lf, model = setup(**options)
    got = main(lf, model, dataset_from(lf, rows), PROMPT)
    print(f'{label:<12} {got["status"]} 빠진 행={got.get("missing")} 오류 행={got.get("errors")}')
    if missing is None:
        assert got["status"] == "완료" and len(got["rows"]) == 4, f"{label}: 네 행 모두 완료여야 해요"
    else:
        assert got["status"] == "EXPERIMENT_HAS_ERRORS", f"{label}: 실패를 잡아야 해요"
        assert (got["missing"], got["errors"]) == (missing, errors), f"{label}: 빠진 행 {missing}, 오류 행 {errors}"
print("\n✅ 정답이에요!")
print("생각해 보기:", "fail_on을 ('식비', '숙박')으로 늘려 두 건이 실패하게 하면 결과가 어떻게 바뀔까요? 그때 04_compare.py는 어디에서 멈출까요? 03_evaluate.py에 이 검사를 넣는다면 어느 줄 뒤에 넣겠어요?")
