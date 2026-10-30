"""준비: 모델 응답 한 건과 Langfuse 점수를 만들어요. uv run --locked 00_start.py"""

from course import connect, answer, finish, save, run


# 첫 모델 응답을 만든 뒤, 완료 점수를 같은 Trace ID에 붙이는 준비 코드예요.
def main():
    lf, model = connect()
    if not lf.auth_check():
        raise RuntimeError("LANGFUSE_AUTH_FAILED")
    row = answer(lf, model, "식비 한도와 필요한 서류는 무엇인가요?")
    # 완료 판정은 Python 코드가 하고, Langfuse는 그 점수를 같은 실행에 연결해 보관해요.
    lf.create_score(
        trace_id=row["trace_id"], name="response_completed", value=1, data_type="BOOLEAN"
    )
    save("result_start.json", row)
    finish(lf, row)
    print("기록 전송을 마쳤어요. Trace 화면에서 GENERATION과 response_completed를 확인하세요.")


if __name__ == "__main__":
    run(main)
