"""3강: 실제 Trace에 수업용 모의 피드백을 연결해요. 실제 사용자가 남긴 평가가 아니에요."""

from course import connect, read, save, run


def main():
    lf, _ = connect()
    # 앞 강의에서 이미 실행한 Trace를 사용해요. 이 파일은 모델을 다시 호출하지 않아요.
    rows = read("result_02.json")
    feedback = []
    # 네 요청 중 두 건에만 피드백이 있어요. 응답하지 않은 두 건을 만족으로 처리하지 않아요.
    for row, value, reason in [
        (rows[0], 0, "설명이 길다는 모의 의견"),
        (rows[1], 1, "간결하다는 모의 의견"),
    ]:
        # 점수는 질문 문장이 아니라 특정 실행의 trace_id에 연결해요.
        lf.create_score(
            trace_id=row["trace_id"],
            name="demo_feedback",
            value=value,
            data_type="BOOLEAN",
            comment="수업용 모의 피드백: " + reason,
        )
        feedback.append({"trace_id": row["trace_id"], "value": value, "reason": reason})
    lf.flush()
    save("result_03.json", {"simulation": True, "feedback": feedback})
    # 응답률 분모는 전체 요청, 긍정 비율 분모는 피드백을 준 요청이에요.
    print("피드백 응답률:", len(feedback) / len(rows))
    print("응답자 중 긍정 비율:", sum(x["value"] for x in feedback) / len(feedback))
    print("낮은 점수의 Trace에서 답변과 근거를 직접 확인하세요.")


if __name__ == "__main__":
    run(main)
