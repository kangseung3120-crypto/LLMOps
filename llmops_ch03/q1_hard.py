# -*- coding: utf-8 -*-
# 3장 1강 퀴즈: 장애 상황의 rows로 대시보드를 다시 읽어요 (Hard: TODO를 직접 완성해요)
# 이 폴더에서 uv run q1_hard.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
import quiz_lab  # noqa: F401  (한글 출력 설정)
from metrics import summarize


def row(ms):
    return {"status": "completed", "latency_ms": ms, "cost_usd": 0.001}


# 01_metrics.py의 rows와 같은 모양으로, 평소 요청 20건을 만들었어요.
NORMAL = [row(200)] * 18 + [row(900)] * 2


# 상황: 장애가 났어요. 느리던 요청이 시간 초과로 끝나 지연값이 사라졌어요.
def incident(rows, limit_ms):
    out = []
    for r in rows:
        if r["status"] == "completed" and r["latency_ms"] > limit_ms:
            out.append({**r, "status": "timeout", "latency_ms": None})
        else:
            out.append(r)
    return out


def read_dashboard(before, after):
    looks_faster = after["p95_ms"] < before["p95_ms"]
    completed_fell = (after["completed"] / after["requests"]
                      < looks_faster)
    return "장애 의심" if looks_faster and completed_fell else "정상 범위"



# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
before = summarize(NORMAL)
changed = incident(NORMAL, 800)
assert sum(r["status"] == "timeout" for r in changed) == 2, "느린 두 요청의 status가 timeout이어야 해요"
during = summarize(changed)
tuned = summarize([row(200)] * 18 + [row(500)] * 2)  # 실제로 빨라진 경우
for label, s in (("평소", before), ("장애", during), ("실제 개선", tuned)):
    print(f'{label:<6} 완료={s["completed"]}/{s["requests"]} 오류율={s["error_rate"]} 미확인={s["unknown"]} p95={s["p95_ms"]}')
assert before["p95_ms"] == 900
assert during["p95_ms"] == 200, "느린 요청이 표본에서 빠져 p95가 좋아져 보여야 해요"
assert during["error_rate"] == 0.0 and during["unknown"] == 2, "timeout은 failed가 아니라서 오류율은 0, 미확인이 2예요"
assert during["requests"] == 20 and during["completed"] == 18
assert read_dashboard(before, during) == "장애 의심", "지연이 좋아 보여도 완료율이 떨어졌어요"
assert read_dashboard(before, tuned) == "정상 범위", "완료율이 그대로면 실제 개선일 수 있어요"
print("대시보드 판독:", read_dashboard(before, during), "/ 실제 개선:", read_dashboard(before, tuned))
print("\n✅ 정답이에요!")
print("생각해 보기:", "limit_ms를 150으로 낮춰 전부 시간 초과가 되게 하면 어떻게 될까요(p95가 None이에요)? read_dashboard가 멈추지 않게 하려면 무엇을 더 검사해야 할까요? timeout을 failed로 세면 어떤 지표가 달라질까요?")
