# -*- coding: utf-8 -*-
# 3장 3강 퀴즈: 버튼을 여러 번 누른 상황으로 피드백을 다시 기록해요 (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q3_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
from quiz_lab import setup
from course import answer

QUESTIONS = ["식비 한도와 필요한 서류는 무엇인가요?", "출장 숙박비 한도는 얼마인가요?"]


# 상황: 실제 버튼을 달았더니 중복 클릭과 지난주 Trace의 클릭이 섞여 들어와요.
def main(lf, rows, clicks):
    known = {r["trace_id"] for r in rows}
    for c in clicks:
        if c["trace_id"] not in known:
            continue
        lf.create_score(trace_id=c["trace_id"], name="user_feedback",
                        value=c["value"], data_type="BOOLEAN",
                        score_id=f'{c["trace_id"]} - {c["user"]}')
    scores = lf.scores_named("user_feedback")
    answered = {s["trace_id"] for s in scores}
    positive = sum(s["value"] for s in scores)
    return {"response_rate": len(answered) / len(rows),
            "positive_rate": positive / len(scores) if scores else None}

# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
def run(make_clicks):
    # 02_measure.py처럼 진짜 answer()로 네 요청을 만든 뒤 그 Trace에 클릭을 연결해요.
    lf, model = setup()
    rows = [answer(lf, model, q, version=v) for q in QUESTIONS for v in ("before", "after")]
    return main(lf, rows, make_clicks([r["trace_id"] for r in rows]))


def click(trace, user, value):
    return {"trace_id": trace, "user": user, "value": value}


cases = [
    ("03_feedback과 같은 상황", lambda t: [click(t[0], "u1", 0), click(t[1], "u2", 1)], 0.5, 0.5),
    ("더블 클릭", lambda t: [click(t[0], "u1", 0), click(t[0], "u1", 0), click(t[1], "u2", 1)], 0.5, 0.5),
    ("마음을 바꿈", lambda t: [click(t[0], "u1", 0), click(t[0], "u1", 1), click(t[1], "u2", 1)], 0.5, 1.0),
    ("한 답변에 두 사람", lambda t: [click(t[0], "u1", 1), click(t[0], "u2", 0)], 0.25, 0.5),
    ("지난주 Trace", lambda t: [click(t[0], "u1", 1), click("old-trace", "u9", 0)], 0.25, 1.0),
    ("클릭 없음", lambda t: [], 0.0, None),
]
for label, make_clicks, rate, positive in cases:
    got = run(make_clicks)
    print(f'{label:<16} 응답률={got["response_rate"]} 긍정 비율={got["positive_rate"]}')
    assert got == {"response_rate": rate, "positive_rate": positive}, f"{label}: 응답률 {rate}, 긍정 비율 {positive}이어야 해요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "score_id를 trace_id만으로 만들면 어느 사례가 틀어질까요? 직접 바꿔서 실패하는 사례를 확인해 보세요. 03_feedback.py를 두 번 실행했을 때 점수가 추가될 수 있는 이유도 여기에 있어요.")
