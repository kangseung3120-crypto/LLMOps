"""2강: 모델과 관측 도구에 보내기 전에 이메일을 제거해요. 실제 모델 호출 1회."""

from course import connect, answer, finish, save, run
from guards import redact, mask_spans


def main():
    # 관측 마스킹 함수를 SDK 생성 시 연결해요. 모델 입력 전처리는 아래에서 별도로 수행해요.
    lf, model = connect(mask_otel_spans=mask_spans)
    original = "demo.student@example.com의 식비 한도와 필요한 서류는 무엇인가요?"
    # 입력 문자열을 바꾸는 단계예요. 원본 대신 이 반환값만 answer에 전달해요.
    safe_question = redact(original)
    # CallbackHandler가 보기 전부터 안전한 입력을 만들어요. 원문은 Trace나 결과 파일에 넣지 않아요.
    row = answer(lf, model, safe_question)
    # 모델이 원문 이메일을 답변에 재생성하면 사용자에게 표시하기 전에 실패로 처리해요.
    if "demo.student@example.com" in row["answer"]:
        raise RuntimeError("PII_IN_OUTPUT")
    save("result_02.json", row)
    finish(lf, row)
    print("원문 이메일 대신 [EMAIL]이 기록되는지 입력과 출력을 확인하세요.")


if __name__ == "__main__":
    run(main)
