"""3강: 문서 검색과 업무 조회를 구분해 관측해요. 실제 외부 업무 시스템은 호출하지 않아요."""

from course import connect, answer, finish, save, run


def main():
    lf, model = connect()
    # 전체 요청을 먼저 열어 업무 조회와 QA가 같은 Trace 아래에 있도록 해요.
    with lf.start_as_current_observation(
        name="qa-with-business-lookup",
        as_type="span",
        metadata={"synthetic": True, "lookup_source": "local-fixture"},
    ) as request:
        # 업무 조회의 입력과 출력 경계를 직접 기록해요. 이 작은 사전은 수업용 모의 DB예요.
        with lf.start_as_current_observation(
            name="lookup-approval", as_type="tool", input={"request_id": "REQ-DEMO-01"}
        ) as tool:
            approval = {"request_id": "REQ-DEMO-01", "status": "승인", "amount": "8만원"}
            tool.update(output=approval)
        # 승인 8만원은 개별 요청의 결과이고 규정 한도 10만원과 달라요.
        # 출처 approval을 붙여 모델이 두 사실을 구분할 수 있게 전달해요.
        row = answer(
            lf,
            model,
            "출장 숙박비 한도와 REQ-DEMO-01의 승인 상태는 무엇인가요?",
            extra_context=f"\n[approval] 요청 {approval['request_id']}: {approval['status']}, {approval['amount']}",
        )
        # 중첩 span도 같은 Trace에 속해요. 도구 조회와 모델 생성의 비용을 혼동하지 않아요.
        request.update(output={"status": row["status"]})
    save("result_03.json", row)
    finish(lf, row)
    print("업무 조회: 모의 DB / 답변 생성: 실제 모델 API")


if __name__ == "__main__":
    run(main)
