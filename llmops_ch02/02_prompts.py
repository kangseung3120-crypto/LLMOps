"""2강: 같은 이름의 프롬프트 두 버전을 저장하고 버전 번호를 고정해요."""

from course import connect, save, new_name, run, POLICY


def main():
    lf, _ = connect()
    # 한 번 실행할 때 생성한 이름 안에 기준선과 후보를 두 버전으로 등록해요.
    name = new_name("llmops-policy")
    # 첫 버전은 근거와 답변 형식의 계약이 약해요. 후보 버전에서 출처와 보류 규칙을 명확히 해요.
    baseline = lf.create_prompt(
        name=name,
        type="text",
        prompt="사내 규정 질문에 짧게 답하세요. 주어진 근거를 참고하세요.",
    )
    # POLICY의 전체 문장은 course.py와 강의 본문에 있어요. 출처와 보류 조건을 포함해요.
    candidate = lf.create_prompt(name=name, type="text", prompt=POLICY)
    # latest 라벨 대신 정확한 버전 번호를 저장해 다음 실행에서도 같은 프롬프트를 읽어요.
    save(
        "result_02.json",
        {"name": name, "baseline": baseline.version, "candidate": candidate.version},
    )
    print("프롬프트:", name)
    print("기준선 버전:", baseline.version, "/ 후보 버전:", candidate.version)
    print("모델, 문서, 검색, 평가기는 고정하고 프롬프트만 비교해요.")


if __name__ == "__main__":
    run(main)
