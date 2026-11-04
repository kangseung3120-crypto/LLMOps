"""1강: 권한 확인이 본문 읽기보다 먼저 일어나는지 확인해요. 모델 호출 없음."""

from course import connect, save, run
from guards import read_document


def main():
    lf, _ = connect()
    # 로그인 서버의 인증 결과를 대신하는 고정 값이에요. 질문에서 받은 조직을 사용하지 않아요.
    principal = {"user_id": "student-demo", "tenant": "campus"}
    read_ids, outcomes = [], []
    # 권한 있는 문서와 없는 문서를 같은 함수에 넣어 실제 읽기 목록까지 비교해요.
    for doc_id in ("meal", "secret"):
        with lf.start_as_current_observation(
            name="document-access",
            as_type="span",
            input={"document_id": doc_id},
            metadata={"synthetic": True},
        ) as span:
            try:
                read_document(doc_id, principal, read_ids)
                outcome = "allowed"
            except PermissionError:
                outcome = "blocked"
            # 비공개 문서의 본문과 사용자 입력 전체를 로그에 남기지 않아요.
            span.update(output={"outcome": outcome})
            outcomes.append({"doc_id": doc_id, "outcome": outcome, "trace_id": span.trace_id})
            print(doc_id, outcome)
    if read_ids != ["meal"]:
        raise RuntimeError("UNAUTHORIZED_READ")
    lf.flush()
    save("result_01.json", {"outcomes": outcomes, "read_ids": read_ids})
    print("실제로 읽은 문서:", read_ids)


if __name__ == "__main__":
    run(main)
