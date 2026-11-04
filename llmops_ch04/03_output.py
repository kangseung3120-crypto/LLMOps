"""3강: 실제 JSON 답변 한 건을 검사하고 잘못된 모의 출력 두 건과 비교해요."""

from pydantic import ValidationError
from course import connect, answer, save, run, POLICY
from guards import Answer


# 입력은 모델의 JSON 문자열과 이번 요청에서 검색된 문서 ID 목록이에요.
# 반환하는 Answer 객체만 다음 단계에 사용하며, 검사 실패 시 예외가 발생해요.
def validate_output(text, allowed_ids):
    # JSON 구문, 필드 타입, answered/abstained와 출처의 관계를 먼저 검사해요.
    parsed = Answer.model_validate_json(text)
    # 출처가 존재하기만 해서는 부족해요. 이번 요청에 실제 전달한 범위 안이어야 해요.
    if not set(parsed.citations) <= set(allowed_ids):
        raise ValueError("검색 결과에 없는 출처예요.")
    return parsed


def main():
    lf, model = connect()
    instruction = (
        POLICY
        + ' JSON 객체만 출력하세요. 형식: {"status":"answered 또는 abstained","answer":"답변 본문","citations":["문서ID"]}. 출처는 citations에만 넣으세요.'
    )
    row = answer(lf, model, "교육비 한도와 증빙 서류는 무엇인가요?", instruction=instruction)
    parsed = validate_output(row["answer"], row["document_ids"])
    # output_valid는 형식과 출처 범위 통과를 뜻해요. 답변의 사실 정확성 점수와는 달라요.
    lf.create_score(
        trace_id=row["trace_id"], name="output_valid", value=1, data_type="BOOLEAN"
    )
    print("실제 응답 검사:", parsed.model_dump())
    rejected = 0
    # 출력 검사가 실패하면 외부 도구로 넘기지 않아요. 모델을 자동 재호출하지도 않아요.
    for bad in [
        '{"status":"answered","answer":"답변","citations":[]}',
        '{"status":"answered","answer":"답변","citations":["secret"]}',
    ]:
        try:
            validate_output(bad, row["document_ids"])
        except (ValueError, ValidationError):
            rejected += 1
    if rejected != 2:
        raise RuntimeError("INVALID_OUTPUT_ACCEPTED")
    lf.flush()
    save(
        "result_03.json",
        {"live": row, "validated": parsed.model_dump(), "mock_rejected": rejected},
    )
    print("잘못된 모의 출력 차단:", rejected, "/ 2")


if __name__ == "__main__":
    run(main)
