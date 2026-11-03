"""1강: 지표의 분모와 누락값을 모의 요청 5개로 확인해요. 외부 API 호출 없음."""

from course import save, run
from metrics import summarize


def main():
    # 비용이 없는 두 요청은 0원이 아니에요. 실패한 요청도 비용이 발생할 수 있어요.
    rows = [
        {"status": "completed", "latency_ms": 100, "cost_usd": 0.001},
        {"status": "completed", "latency_ms": 200, "cost_usd": 0.002},
        {"status": "completed", "latency_ms": 900, "cost_usd": None},
        {"status": "failed", "latency_ms": 300, "cost_usd": 0.001},
        {"status": "unknown", "latency_ms": None, "cost_usd": None},
    ]
    # 요청 5건이 전체 분모예요. 완료 지연 3건과 알려진 비용 3건은 서로 다른 집합이에요.
    result = summarize(rows)
    # 모의 자료 표시를 함께 저장해 실제 운영 요청으로 오해하지 않게 해요.
    save("result_01.json", {"simulation": True, "summary": result})
    for key, value in result.items():
        print(key, value)


if __name__ == "__main__":
    run(main)
