"""1강: 가상 규정 질문 6개를 검사하고 Langfuse에 dev/holdout 데이터셋을 만들어요."""

import hashlib
import json
from course import connect, read, save, new_name, run, DOCUMENTS


# 입력은 golden.json의 질문 목록이에요. 등록 전에 ID와 기대값의 모순을 확인해요.
# 통과하면 반환값 없이 끝나고, 오류가 있으면 등록 단계로 진행하지 않아요.
def validate(rows):
    # 질문 ID는 두 실험을 연결하는 키예요. 중복되면 어떤 답끼리 비교할지 모호해져요.
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("질문 ID가 중복돼요.")
    allowed = {d["id"] for d in DOCUMENTS}
    for row in rows:
        expected = row["expected"]
        if row["split"] not in {"dev", "holdout"} or not row["question"].strip():
            raise ValueError("split과 question을 확인하세요.")
        if (
            set(expected) != {"terms", "citations", "abstain"}
            or type(expected["abstain"]) is not bool
        ):
            raise ValueError("expected 형식이 일치하지 않아요.")
        # 출처 정답은 이번 가상 문서에 존재해야 해요. 모델 출력에 맞춰 임의로 추가하지 않아요.
        if not set(expected["citations"]) <= allowed:
            raise ValueError("존재하지 않는 출처 ID예요.")
        # 답이 없는 사례는 보류가 기대 행동이에요. 필수 표현과 출처를 요구하면 기준이 충돌해요.
        if expected["abstain"] and (expected["terms"] or expected["citations"]):
            raise ValueError("보류 질문에는 정답 표현과 출처를 넣지 않아요.")


def main():
    rows = read("golden.json")
    validate(rows)
    lf, _ = connect()
    names = {}
    for split in ("dev", "holdout"):
        name = new_name("llmops-" + split)
        # dev와 holdout을 별개 데이터셋으로 만들어 확인용 질문이 수정 단계에 섞이지 않게 해요.
        lf.create_dataset(name=name, description="수업용 가상 규정 QA / " + split)
        for row in [r for r in rows if r["split"] == split]:
            # 모델이 볼 질문과 평가기만 볼 기대값을 분리해 등록해요.
            # kind와 split은 사례 분류용 metadata이며 모델 프롬프트에는 넣지 않아요.
            lf.create_dataset_item(
                dataset_name=name,
                input={"id": row["id"], "question": row["question"]},
                expected_output=row["expected"],
                metadata={"split": split, "kind": row["kind"]},
            )
        names[split] = name
        print(split, name)
    # 같은 데이터로 비교했는지 확인할 해시와 데이터셋 이름만 다음 단계에 넘겨요.
    digest = hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    save("result_01.json", {"datasets": names, "dataset_hash": digest})
    print("검사 완료: dev 4개, holdout 2개 / 모델 호출 없음")


if __name__ == "__main__":
    run(main)
