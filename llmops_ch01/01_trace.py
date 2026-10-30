"""1강: 같은 요청의 질문, 검색 결과, 생성 답변을 하나의 Trace로 연결해요."""

from course import connect, answer, finish, save, run


def main():
    # 설정에서 두 연결 객체를 만들고 같은 질의응답 함수에 전달해요.
    lf, model = connect()
    # 수정할 곳: 질문을 교육비 또는 출장 숙박비로 바꾼 뒤 검색 단계부터 확인하세요.
    row = answer(lf, model, "교육비 한도와 증빙 서류는 무엇인가요?")
    # row에는 답변뿐 아니라 문서 ID, Trace ID, 시작 시각과 사용량도 있어요.
    # 저장한 Trace ID를 다음 강의가 다시 읽으므로 이 파일을 먼저 실행해요.
    save("result_01.json", row)
    print("검색한 문서:", row["document_ids"])
    finish(lf, row)


if __name__ == "__main__":
    run(main)
