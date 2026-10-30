# -*- coding: utf-8 -*-
# 1장 2강 퀴즈: 재조회 결과만 보고 모델 실행 기록을 판정해요 (정답 코드예요)
# 이 폴더에서 uv run q2_solution.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

from datetime import datetime, timezone
from types import SimpleNamespace as Obs

# 서버 재조회 결과를 흉내 낸 고정 자료예요. Langfuse를 호출하지 않아요.
T = datetime(2026, 1, 1, tzinfo=timezone.utc)
full = [
    Obs(name="ChatOpenAI", type="GENERATION", end_time=T),
    Obs(name="ChatPromptTemplate", type="CHAIN", end_time=T),
    Obs(name="generate-answer", type="CHAIN", end_time=T),
    Obs(name="policy-qa", type="SPAN", end_time=T),
    Obs(name="retrieve", type="SPAN", end_time=T),
]


# 02_read_trace.py처럼 조회 결과만 보고 판정하세요. 모델을 다시 호출하지 않아요.
def judge(observations):
    if not observations:
        return "조회 결과 없음"
    generations = [x for x in observations if x.type.upper() == "GENERATION"]
    if not generations or any(x.end_time is None for x in generations):
        return "GENERATION_NOT_CONFIRMED"
    return "서버 기록 확인"


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
cases = [
    ("실행 직후 조회", [], "조회 결과 없음"),
    ("검색 span만 있음", full[3:], "GENERATION_NOT_CONFIRMED"),
    ("생성 미완료", [Obs(name="ChatOpenAI", type="GENERATION", end_time=None), *full[1:]], "GENERATION_NOT_CONFIRMED"),
    ("소문자 type", [Obs(name="ChatOpenAI", type="generation", end_time=T)], "서버 기록 확인"),
    ("정상 5개", full, "서버 기록 확인"),
]
for label, observations, want in cases:
    got = judge(observations)
    print(f"{label:<12} 관측 {len(observations)}개 -> {got}")
    assert got == want, f"{label}: {want}이어야 해요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "'서버 기록 확인'이 나오면 답변이 정답이라는 뜻일까요? 정답 여부를 판단하려면 무엇을 더 확인해야 하나요?")
