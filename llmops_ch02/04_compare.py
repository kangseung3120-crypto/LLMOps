"""4강: 같은 ID끼리 비교하고, 통과한 후보만 holdout 2개에서 확인해요."""

from course import connect, read, save, run
from evaluation import experiment


def compare(report):
    # 목록 순서가 바뀌어도 같은 질문끼리 비교하도록 ID를 키로 바꿔요.
    before, after = [
        {r["id"]: r for r in report[label]["rows"]} for label in ("baseline", "candidate")
    ]
    if (
        any(len(report[label]["rows"]) != 4 for label in ("baseline", "candidate"))
        or len(before) != 4
        or len(after) != 4
        or set(before) != set(after)
    ):
        raise ValueError("비교할 ID가 누락되었거나 중복돼요.")
    if any(
        r["error"] or "rule_pass" not in r["scores"]
        for r in [*before.values(), *after.values()]
    ):
        return {"decision": "BLOCK", "reason": "평가 실패 또는 점수 누락"}
    # 질문별 후보 점수에서 기준선 점수를 빼요. 음수인 질문은 평균과 관계없이 회귀예요.
    delta = {
        key: after[key]["scores"]["rule_pass"] - before[key]["scores"]["rule_pass"]
        for key in before
    }
    passed = sum(r["scores"]["rule_pass"] for r in after.values())
    # 이 작은 수업 데이터의 기준이에요. 운영 승인 기준으로 그대로 옮기지 마세요.
    accepted = passed == 4 and min(delta.values()) >= 0
    return {
        "decision": "CHECK_HOLDOUT" if accepted else "BLOCK",
        "delta": delta,
        "candidate_passed": passed,
        "count": 4,
    }


def main():
    report = read("result_03.json")
    result = compare(report)
    print("dev 판정:", result)
    # dev를 통과한 경우에만 holdout 모델 호출이 발생해요. BLOCK이면 추가 호출하지 않아요.
    if result["decision"] == "CHECK_HOLDOUT":
        lf, model = connect()
        names = read("result_01.json")["datasets"]
        prompt = lf.get_prompt(
            report["prompts"]["name"],
            version=report["prompts"]["candidate"],
            cache_ttl_seconds=0,
        )
        holdout = experiment(
            lf, model, lf.get_dataset(names["holdout"]), prompt, "candidate-holdout"
        )
        result["holdout"] = holdout
        # 확인 질문 2개가 모두 평가됐고 오류 없이 통과해야 REVIEW로 진행해요.
        all_passed = len(holdout["rows"]) == 2 and all(
            not r["error"] and r["scores"].get("rule_pass") == 1 for r in holdout["rows"]
        )
        result["decision"] = "REVIEW" if all_passed else "BLOCK"
        lf.flush()
        print("holdout:", holdout["url"])
    save("result_04.json", result)
    print(
        "최종 판정:",
        result["decision"],
        "/ 소규모 확인이므로 운영 배포는 자동 승인하지 않아요.",
    )


if __name__ == "__main__":
    run(main)
