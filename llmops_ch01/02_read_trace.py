"""2강: 새 모델 호출 없이 1강의 실행을 Langfuse에서 다시 조회해요."""

from datetime import datetime, timedelta, timezone
from course import connect, read, save, run


def main():
    lf, _ = connect()
    # 앞 강의에서 받은 답변을 다시 생성하지 않고 기존 실행의 식별자를 가져와요.
    row = read("result_01.json")
    # UTC 시작 시각 앞뒤에 여유를 두고 같은 Trace만 조회해요.
    # 반환 목록의 순서 대신 각 observation의 이름, 종류, 부모 관계로 구조를 읽어요.
    observations = lf.api.observations.get_many(
        trace_id=row["trace_id"],
        limit=30,
        fields="core,basic,usage,model,io",
        from_start_time=datetime.fromisoformat(row["started_at"]) - timedelta(minutes=1),
        to_start_time=datetime.now(timezone.utc) + timedelta(minutes=1),
    ).data
    # flush 성공은 서버 조회 성공과 달라요. 전송 직후에는 검색 반영이 늦을 수 있어요.
    if not observations:
        raise ValueError("조회 결과가 아직 없어요. 잠시 뒤 이 파일만 다시 실행하세요.")
    for item in observations:
        print(item.name, item.type, "완료" if item.end_time else "미완료")
    # 검색 span까지 모델 호출로 세지 않도록 GENERATION만 골라요.
    # 종료 시각은 실행 기록의 완료 증거이며, 답변의 정확성은 별도로 평가해요.
    generations = [x for x in observations if x.type.upper() == "GENERATION"]
    if not generations or any(x.end_time is None for x in generations):
        raise RuntimeError("GENERATION_NOT_CONFIRMED")
    save(
        "result_02.json",
        {
            "trace_id": row["trace_id"],
            "observation_count": len(observations),
            "generation_complete": True,
        },
    )
    print("서버 재조회 완료:", len(observations), "개 observation")


if __name__ == "__main__":
    run(main)
