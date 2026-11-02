"""3강: dev 4개 × 두 버전, 총 8번 모델을 호출해요."""

import hashlib
from pathlib import Path
from course import connect, read, save, run
from evaluation import experiment


def main():
    lf, model = connect()
    # 앞의 두 강의가 만든 데이터셋 이름과 프롬프트 버전이 실험 입력이에요.
    data_info, prompts = read("result_01.json"), read("result_02.json")
    dataset = lf.get_dataset(data_info["datasets"]["dev"])
    # 결과에 모델, 데이터와 평가기 해시를 남겨 비교 조건이 바뀌었는지 확인해요.
    results = {
        "dataset_hash": data_info["dataset_hash"],
        "dataset_name": dataset.name,
        "model": model.model_name,
        "evaluator_hash": hashlib.sha256(Path("evaluation.py").read_bytes()).hexdigest(),
        "prompts": prompts,
    }
    # 질문과 평가기는 유지한 채 프롬프트 버전만 교체해요. dev 4개를 두 번 호출해요.
    for label in ("baseline", "candidate"):
        prompt = lf.get_prompt(prompts["name"], version=prompts[label], cache_ttl_seconds=0)
        # experiment는 생성 Task와 평가 함수를 연결하고 질문별 답변, 점수, 오류를 반환해요.
        results[label] = experiment(lf, model, dataset, prompt, label)
        print(label, results[label]["url"])
    lf.flush()
    save("result_03.json", results)
    # 실패 항목이 있어도 결과는 먼저 보존해요. 실패를 평균에서 조용히 제외하지 않아요.
    if any(r["error"] for label in ("baseline", "candidate") for r in results[label]["rows"]):
        raise RuntimeError("EXPERIMENT_HAS_ERRORS")
    print("dev 평가 완료: 각 질문의 rule_pass와 답변을 함께 읽으세요.")


if __name__ == "__main__":
    run(main)
