"""2강: 같은 두 질문에 불필요한 문맥 유무만 바꿔 실제 4회 호출해요."""

from course import connect, answer, save, run


def main():
    lf, model = connect()
    rows = []
    # 수정할 곳: 대표 질문을 추가할 수 있어요. before와 after에는 반드시 같은 질문을 사용해요.
    questions = ["식비 한도와 필요한 서류는 무엇인가요?", "출장 숙박비 한도는 얼마인가요?"]
    # 한 질문씩 before/after를 번갈아 실행해 시간 순서 효과를 조금 줄여요.
    # 중요한 근거는 유지하고 관계없는 문장만 제거하는 변경이에요.
    for index, question in enumerate(questions):
        for version in ("before", "after"):
            padding = (
                "\n참고: 회사 정원에는 나무가 있습니다." * 60 if version == "before" else ""
            )
            # answer 내부에서 실제 usage_metadata와 요청 처리 시간을 측정해 반환해요.
            row = answer(lf, model, question, extra_context=padding, version=version)
            row["case_id"] = f"q{index + 1}"
            # 원화/달러 환산이나 임의 단가를 적용하지 않아요. 서버의 비용 필드는 다음 강의에서 읽어요.
            row["cost_usd"] = None
            rows.append(row)
            print(version, row["case_id"], "ms", row["latency_ms"], "usage", row["usage"])
    lf.flush()
    # case_id와 app_version을 함께 남겨 같은 질문의 변경 전후를 대응시켜요.
    save("result_02.json", rows)
    print("Trace:", lf.get_trace_url(trace_id=rows[0]["trace_id"]))


if __name__ == "__main__":
    run(main)
