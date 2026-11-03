# -*- coding: utf-8 -*-
# 3장 4강 퀴즈: 가격을 모르는 모델로 바꾼 상황을 판정해요 (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q4_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
from quiz_lab import setup
from course import answer
from metrics import summarize

QUESTIONS = ["식비 한도와 필요한 서류는 무엇인가요?", "출장 숙박비 한도는 얼마인가요?"]


# 상황: 후보 모델로 바꿨더니 서버가 가격을 몰라요. 판정도 고정값 대신 계산해요.
def main(lf, rows, min_samples):
    for row in rows:
        data = lf.api.observations.get_many(
            trace_id=row["trace_id"]).data
        costs = [o.total_cost for o in data if o.type.upper() == "GENERATION"]
        row["cost_usd"] = (sum(costs) if costs and
                           all(c is not None for c in costs) else None)
    b, a = [summarize([r for r in rows if r["app_version"] == v])
            for v in ("before", "after")]
    if a["completed"] < min_samples:
        return "REVIEW: 표본 부족", b, a
    if a["cost_coverage"] < 1.0:
        return "REVIEW: 비용 미확인", b, a
    if a["total_cost_usd"] > b["total_cost_usd"]:
        return "REVIEW: 비용 증가", b, a
    return "유지 후보", b, a


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
PADDING = "\n참고: 회사 정원에는 나무가 있습니다." * 60


def run(after_padding, before_padding=PADDING, unpriced_after=(), repeat=1, min_samples=2):
    # 02_measure.py처럼 진짜 answer()로 요청을 만들어요. 토큰과 비용은 설명용 값이에요.
    lf, model = setup()
    rows = []
    for _ in range(repeat):
        for q in QUESTIONS:
            rows.append(answer(lf, model, q, extra_context=before_padding, version="before"))
            model.priced = not unpriced_after
            rows.append(answer(lf, model, q, extra_context=after_padding, version="after"))
            model.priced = True
    return main(lf, rows, min_samples)


cases = [
    ("교안처럼 버전당 2건", dict(after_padding="", min_samples=20), "REVIEW: 표본 부족"),
    ("문맥 축소, 표본 충분", dict(after_padding="", repeat=10, min_samples=20), "유지 후보"),
    ("문맥이 오히려 늘어남", dict(after_padding=PADDING * 2, repeat=10, min_samples=20), "REVIEW: 비용 증가"),
    ("가격 미확인 모델", dict(after_padding="", unpriced_after=True, repeat=10, min_samples=20), "REVIEW: 비용 미확인"),
]
for label, options, want in cases:
    got, b, a = run(**options)
    print(f'{label:<14} {got:<14} before ${b["known_cost_usd"]:.6f} / after 알려진 비용 {a["known_cost_usd"]} 파악률 {a["cost_coverage"]}')
    assert got == want, f"{label}: {want}이어야 해요"
got, b, a = run(after_padding="", repeat=1, min_samples=2)
per_request = b["total_cost_usd"] / b["requests"]
assert per_request < 0.0009, "부모 span 비용까지 더하면 요청 비용이 부풀어요. GENERATION만 더하세요"
got, b, a = run(after_padding="", unpriced_after=True, min_samples=2)
assert a["known_cost_usd"] is None and a["total_cost_usd"] is None, "가격을 모르면 0원이 아니라 None이에요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "가격 미확인 모델을 0원으로 치면 판정이 어떻게 바뀔까요? 이 판정기에는 답변 품질 조건이 없어요. 3장 2강처럼 필수 사실 검사를 넣는다면 어느 줄에 넣어야 할까요?")
