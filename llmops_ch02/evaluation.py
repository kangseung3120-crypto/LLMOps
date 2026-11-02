"""같은 평가기를 두 프롬프트 버전에 사용해요. 문자열 규칙의 범위를 넘겨 해석하지 마세요."""

import re
from langfuse import Evaluation
from course import answer


# output은 Task가 반환한 답변 딕셔너리, expected_output은 데이터셋의 기대값이에요.
# 반환하는 Evaluation 목록을 SDK가 실험 항목과 Trace에 연결해요.
def evaluate(*, output, expected_output, **kwargs):
    if not output or output.get("status") != "completed":
        raise ValueError("완료되지 않은 응답은 품질 점수로 바꾸지 않아요.")
    text = re.sub(r"\s+", "", output["answer"])
    expected = expected_output
    # 숫자의 쉼표와 공백만 정규화해요. 의미상 같은 다른 표현까지 판단하지는 못해요.
    text = text.replace(",", "")
    # 필수 표현이 전부 있어야 통과해요. 보류 사례는 terms가 비어 이 검사만 통과하며,
    # 출처와 보류 행동 검사까지 통과해야 최종 rule_pass가 1이 돼요.
    terms_ok = all(term in text for term in expected["terms"])
    # 대괄호 안의 ID를 모두 비교해요. 숫자나 대문자가 섞인 가짜 출처도 누락하지 않아요.
    # 순서와 중복 횟수는 평가하지 않아요.
    citations = set(re.findall(r"\[([^\[\]]*)\]", text))
    citation_ok = citations == set(expected["citations"])
    # 이 예제는 고정된 보류 표현만 검사해요. 의미가 같은 모든 문장을 판별하지는 못해요.
    abstained = "확인할수없" in text
    behavior_ok = abstained == expected["abstain"]
    passed = terms_ok and citation_ok and behavior_ok
    return [
        Evaluation(name="required_terms", value=int(terms_ok), data_type="BOOLEAN"),
        Evaluation(name="citation_match", value=int(citation_ok), data_type="BOOLEAN"),
        Evaluation(name="answer_behavior", value=int(behavior_ok), data_type="BOOLEAN"),
        Evaluation(
            name="rule_pass",
            value=int(passed),
            data_type="BOOLEAN",
            comment="정해진 표현, 출처 ID, 보류 표현 검사. 의미 정확성 전체를 보장하지 않음",
        ),
    ]


def experiment(lf, model, dataset, prompt, label):
    # SDK가 데이터셋 항목을 하나씩 전달해요. expected_output은 모델에 넘기지 않아요.
    def task(*, item, **kwargs):
        return answer(
            lf, model, item.input["question"], instruction=prompt.prompt, version=label
        )

    # task 출력이 evaluate의 output으로 이어져요. 순차 실행으로 호출량을 작게 유지해요.
    result = dataset.run_experiment(
        name=label,
        task=task,
        evaluators=[evaluate],
        max_concurrency=1,
        metadata={
            "prompt_name": prompt.name,
            "prompt_version": prompt.version,
            "evaluator": "rules-v2",
            "synthetic": True,
        },
    )
    # SDK는 항목 오류도 결과에 담아요. 오류를 0점이나 정상 답변으로 바꾸지 않고 별도로 보존해요.
    rows = []
    for item in result.item_results:
        rows.append(
            {
                "id": item.item.input["id"],
                "output": item.output,
                "scores": {e.name: e.value for e in item.evaluations},
                "error": None
                if item.output and len(item.evaluations) == 4
                else "INCOMPLETE_EVALUATION",
                "trace_id": item.trace_id,
            }
        )
    return {"url": result.dataset_run_url, "rows": rows}
