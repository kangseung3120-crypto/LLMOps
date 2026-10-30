# -*- coding: utf-8 -*-
# 1장 3강 퀴즈: 부모와 자식 구간의 지연을 중복 없이 읽어요 (Hard: TODO를 직접 완성해요)
# 이 폴더에서 uv run q3_hard.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 03_steps.py의 Trace를 단순화한 설명용 지연 기록이에요 (ms). parent는 부모 구간 이름이에요.
spans = [
    {"name": "qa-with-business-lookup", "parent": None, "ms": 1500},
    {"name": "lookup-approval", "parent": "qa-with-business-lookup", "ms": 100},
    {"name": "policy-qa", "parent": "qa-with-business-lookup", "ms": 1300},
    {"name": "retrieve", "parent": "policy-qa", "ms": 5},
    {"name": "generate-answer", "parent": "policy-qa", "ms": 1280},
]


# 사용자가 기다린 시간과 병목 구간을 구하세요. 자식 시간을 부모에 더하면 중복 계산이에요.
def children(name):
    return [s for s in spans if s["parent"] == name]


root = [s for s in spans if s["parent"] is None][0]
total_ms = root["ms"]
bottleneck = max(children(root["name"]), key=lambda s: s["ms"])
inner = max(children(bottleneck["name"]), key=lambda s: s["ms"])


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
wrong = sum(s["ms"] for s in spans)
print("모든 구간을 더한 값:", wrong, "ms  <- 중복 계산")
print("사용자가 기다린 시간:", total_ms, "ms")
print("병목:", bottleneck["name"], "→", inner["name"])
assert total_ms == 1500, "전체 지연은 바깥 구간 하나로 읽어요"
assert wrong != total_ms
assert bottleneck["name"] == "policy-qa", "업무 조회(100ms)보다 QA(1300ms)가 길어요"
assert inner["name"] == "generate-answer", "QA 안에서는 검색보다 생성이 길어요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "lookup-approval과 policy-qa를 동시에 실행하도록 바꾸면 total_ms는 어떻게 달라질까요? 자식 시간의 합보다 부모가 짧아질 수 있는 이유는?")
