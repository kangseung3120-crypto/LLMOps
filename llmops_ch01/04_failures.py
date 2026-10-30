"""4강: 모의 사례로 실패 판정 규칙을 확인해요. 모델 API를 호출하지 않아요."""

from datetime import datetime
from course import connect, save, run


def classify(row):
    # 필드가 없거나 날짜가 틀렸다면 정상으로 추정하지 않아요.
    if row.get("status") not in {"completed", "failed"}:
        return "incomplete"
    # 시각의 형식뿐 아니라 시간대와 순서까지 검사해요. 잘못된 시각은 오류율의 근거로 쓰지 않아요.
    try:
        start, end = [datetime.fromisoformat(row[key]) for key in ("started_at", "ended_at")]
        if start.tzinfo is None or end.tzinfo is None or end < start:
            return "invalid_time"
    except (KeyError, TypeError, ValueError):
        return "invalid_time"
    # 기록 형식이 유효한 뒤 실행 실패를 분류해요. 위 검사에서 이미 반환됐을 수도 있어요.
    if row["status"] == "failed":
        return "model_error"
    if not row.get("document_ids"):
        return "retrieval_empty"
    return "completed"


def main():
    lf, _ = connect()
    base = {
        "status": "completed",
        "started_at": "2026-01-01T00:00:00+00:00",
        "ended_at": "2026-01-01T00:00:01+00:00",
        "document_ids": ["meal"],
    }
    # base에서 필드 하나씩 바꿔 분류 이유를 비교해요. 실제 API 장애를 발생시키는 코드는 아니에요.
    cases = [
        ("정상", base),
        ("모델 실패", {**base, "status": "failed"}),
        ("검색 없음", {**base, "document_ids": []}),
        ("상태 누락", {**base, "status": None}),
        ("날짜 오류", {**base, "ended_at": "not-a-date"}),
        ("시간 역전", {**base, "ended_at": "2025-12-31T23:59:59+00:00"}),
    ]
    results = []
    for label, sample in cases:
        outcome = classify(sample)
        with lf.start_as_current_observation(
            name="simulated-failure-case",
            as_type="span",
            input=sample,
            metadata={"simulation": True},
        ) as span:
            span.update(
                output={"case": label, "outcome": outcome},
                level="DEFAULT" if outcome == "completed" else "WARNING",
            )
            # 분류값을 현재 모의 Trace에 붙여 입력과 판정을 함께 조회할 수 있게 해요.
            lf.create_score(
                trace_id=span.trace_id,
                name="failure_category",
                value=outcome,
                data_type="CATEGORICAL",
                comment="모의 사례의 판정 결과",
            )
            results.append({"case": label, "outcome": outcome, "trace_id": span.trace_id})
        print(label, "->", outcome)
    lf.flush()
    save("result_04.json", results)


if __name__ == "__main__":
    run(main)
