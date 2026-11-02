# -*- coding: utf-8 -*-
# 2장 2강 퀴즈: 비교 도중 새 버전이 올라온 상황을 재현해요 (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q2_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드를 규칙 모델(가짜)로 돌려요. 답변 · 토큰 · 비용은 설명용이에요.
from quiz_lab import setup
from course import POLICY, answer, new_name, read
from evaluation import evaluate

BASELINE = "사내 규정 질문에 짧게 답하세요. 주어진 근거를 참고하세요."
TEAMMATE = "제공된 근거로만 답하세요. 답변 끝에 [meal]처럼 출처를 붙이세요."


# 상황: 비교 도중 팀원이 같은 이름으로 새 버전을 등록했어요.
def main(lf):
    name = new_name("llmops-policy")
    baseline = lf.create_prompt(name=name, prompt=BASELINE)
    candidate = lf.create_prompt(name=name, prompt=POLICY)
    saved = {"name": name, "baseline": baseline.version,
             "candidate": candidate.version}
    lf.create_prompt(name=name, prompt=TEAMMATE)  # 팀원의 등록
    pinned = lf.get_prompt(name, version=saved["candidate"], cache_ttl_seconds=0)
    latest = lf.get_prompt(name, label="latest", cache_ttl_seconds=0)
    return saved, pinned, latest


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
lf, model = setup()
saved, pinned, latest = main(lf)
print("저장한 버전:", saved["baseline"], saved["candidate"], "/ 번호로 읽은 버전:", pinned.version, "/ latest:", latest.version)
assert (saved["baseline"], saved["candidate"]) == (1, 2), "기준선 1, 후보 2가 저장돼야 해요"
assert pinned.prompt == POLICY, "번호로 읽으면 새 버전이 올라와도 후보 그대로예요"
assert latest.prompt == TEAMMATE, "latest는 팀원의 새 버전을 가리켜요"

# 진짜 answer()와 evaluate()로 같은 보류 질문을 두 프롬프트에 돌려요. 답변은 규칙 모델의 설명용 답이에요.
d04 = next(r for r in read("golden.json") if r["id"] == "d04")
results = {}
for label, prompt in (("번호로 고정", pinned), ("latest", latest)):
    reply = answer(lf, model, d04["question"], instruction=prompt.prompt)
    scores = {e.name: e.value for e in evaluate(output=reply, expected_output=d04["expected"])}
    results[label] = scores["rule_pass"]
    print(f'{label}: {reply["answer"]} -> rule_pass {scores["rule_pass"]}')
assert results == {"번호로 고정": 1, "latest": 0}, "latest로 읽으면 비교 대상이 바뀌어 d04가 실패해요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "TEAMMATE 문구를 고쳐 보류 시 출처를 빼도록 바꾸고 다시 실행해 보세요. latest의 d04 점수가 바뀌나요? 그렇다면 이 새 버전은 다음 비교에서 무엇과 비교해야 할까요?")
