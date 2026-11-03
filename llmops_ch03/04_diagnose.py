"""4강: 서버의 비용을 재조회하고 변경 전후를 비교해요. 추가 모델 호출 없음."""

from datetime import datetime, timedelta, timezone
from time import sleep
from course import connect, read, save, run
from metrics import summarize


def main():
    lf, _ = connect()
    rows = read("result_02.json")
    # 로컬의 Trace ID로 서버 관측을 읽어 비용을 채워요. 다른 시간대나 버전의 실행을 섞지 않아요.
    for row in rows:
        observations = lf.api.observations.get_many(
            trace_id=row["trace_id"],
            limit=30,
            fields="core,basic,usage,model",
            from_start_time=datetime.fromisoformat(row["started_at"]) - timedelta(minutes=1),
            to_start_time=datetime.now(timezone.utc) + timedelta(minutes=1),
        ).data
        # 부모 span과 자식 모델 비용을 함께 더하면 중복될 수 있어 모델 구간만 골라요.
        generations = [o for o in observations if o.type.upper() == "GENERATION"]
        # 비용이 0이면 알려진 0이에요. None이면 아직 집계되지 않았거나 가격을 모르는 상태예요.
        costs = [o.total_cost for o in generations]
        row["cost_usd"] = sum(costs) if costs and all(c is not None for c in costs) else None
        sleep(2.1)  # 무료 계정의 조회 API 제한을 넘지 않도록 요청 간격을 둬요.
    # 같은 app_version끼리 집계해 before와 after를 분리해요.
    summary = {
        v: summarize([r for r in rows if r["app_version"] == v]) for v in ("before", "after")
    }
    for version, values in summary.items():
        print(version, values)
    # 표본 2개로 SLA나 통계적 성능 향상을 주장하지 않아요. 답의 내용과 출처도 함께 확인해요.
    save(
        "result_04.json",
        {"rows": rows, "summary": summary, "decision": "REVIEW", "reason": "버전당 2건"},
    )
    print("판정: REVIEW / 입력 토큰 감소와 답변 품질을 함께 검토하세요.")


if __name__ == "__main__":
    run(main)
