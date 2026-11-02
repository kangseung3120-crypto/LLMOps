# -*- coding: utf-8 -*-
# 2장 4강 퀴즈: 판정 기준이 바뀐 상황으로 compare를 고쳐요 (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q4_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
from types import SimpleNamespace
from quiz_lab import dataset_from, lesson, setup
from course import POLICY, read
from evaluation import experiment


def pair(report):
    # 04_compare.py의 앞부분과 같아요. ID가 어긋나면 멈추고, 질문 ID로 찾을 수 있게 바꿔요.
    before, after = [{r["id"]: r for r in report[k]["rows"]} for k in ("baseline", "candidate")]
    if set(before) != set(after) or len(after) != len(report["candidate"]["rows"]):
        raise ValueError("비교할 ID가 누락되었거나 중복돼요.")
    return before, after


def rule(row):
    return row["scores"]["rule_pass"]


# 상황: 평가셋이 6건으로 늘었어요. 1건 실패는 허용하되 중요 질문의 악화는 막아요.
def compare(report, critical, min_rate):
    before, after = pair(report)
    if any(r["error"] or "rule_pass" not in r["scores"]
           for r in [*before.values(), *after.values()]):
        return {"decision": "BLOCK", "reason": "평가 실패"}
    delta = {k: rule(after[k]) - rule(before[k]) for k in before}
    if any(delta[k] < 0 for k in ____):
        return {"decision": "BLOCK", "reason": "중요 사례 악화",
                "delta": delta}
    rate = sum(rule(r) for r in after.values()) / ____
    decision = "CHECK_HOLDOUT" if rate >= ____ else "BLOCK"
    return {"decision": decision, "delta": delta, "rate": rate}


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
# 진짜 experiment()로 여섯 질문을 실행해 결과를 만들어요. 답변은 규칙 모델의 설명용 답이에요.
rows = read("golden.json")
CRITICAL = ["d04", "t02"]  # 규정 밖 질문은 악화를 허용하지 않아요.
PROMPTS = {"기준선": "사내 규정 질문에 짧게 답하세요. 주어진 근거를 참고하세요.", "후보": POLICY,
           "예시 복사 후보": "제공된 근거로만 답하세요. 답변 끝에 [meal]처럼 출처를 붙이세요."}


def run(text):
    lf, model = setup()
    prompt = SimpleNamespace(name="quiz", version=1, prompt=text)
    return experiment(lf, model, dataset_from(lf, rows), prompt, "run")


def fake(scores):
    return {"rows": [{"id": k, "scores": {"rule_pass": v}, "error": None} for k, v in scores.items()]}


base = run(PROMPTS["기준선"])
good = {k: 1 for k in ("d01", "d02", "d03", "d04", "t01", "t02")}
cases = [
    ("후보 프롬프트", base, run(PROMPTS["후보"]), "CHECK_HOLDOUT"),
    ("예시 복사 후보", base, run(PROMPTS["예시 복사 후보"]), "BLOCK"),
    ("일반 질문 1건 악화", fake(good), fake({**good, "d02": 0}), "CHECK_HOLDOUT"),
    ("일반 질문 2건 악화", fake(good), fake({**good, "d01": 0, "d02": 0}), "BLOCK"),
    ("중요 질문 1건 악화", fake(good), fake({**good, "d04": 0}), "BLOCK"),
]
for label, before, after, want in cases:
    got = compare({"baseline": before, "candidate": after}, CRITICAL, 0.8)
    rate = f'{got["rate"]:.0%}' if "rate" in got else "-"
    print(f'{label:<12} {got["decision"]:<14} 통과율={rate} {got.get("reason", "")}')
    assert got["decision"] == want, f"{label}: {want}이어야 해요"
assert compare({"baseline": fake(good), "candidate": fake({**good, "d04": 0})}, CRITICAL, 0.8)["reason"] == "중요 사례 악화"

# 기준을 원래대로 두면(4건 · 100%) 진짜 04_compare.py와 판정이 같아야 해요.
official = lesson("04_compare").compare
four = {k: 1 for k in ("d01", "d02", "d03", "d04")}
for scores in (four, {**four, "d02": 0}):
    report = {"baseline": fake({**four, "d01": 0}), "candidate": fake(scores)}
    assert compare(report, list(four), 1.0)["decision"] == official(report)["decision"], "원래 기준에서는 04_compare.py와 같아야 해요"
print("원래 기준(100%)에서는 04_compare.py와 판정이 같아요.")
print("\n✅ 정답이에요!")
print("생각해 보기:", "CRITICAL에 d03을 추가하거나 0.8을 0.9로 바꾸면 어떤 사례의 판정이 달라지나요? 이 기준은 결과를 보기 전에 정해야 해요. 왜 그럴까요?")
