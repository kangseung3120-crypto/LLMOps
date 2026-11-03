"""단위를 명시하고 모르는 값은 None으로 남기는 소규모 집계예요."""

from math import ceil
from statistics import median


# 입력은 요청별 status, latency_ms, cost_usd 목록이에요.
# 반환값에는 지표와 함께 집계 건수 및 비용 파악률을 넣어 해석 범위를 남겨요.
def summarize(rows):
    # 완료 지연만 비교하기 위해 상태로 먼저 고르지만, 실패율의 분모는 전체 요청이에요.
    finished = [r for r in rows if r["status"] == "completed"]
    errors = sum(r["status"] == "failed" for r in rows)
    unknown = sum(r["status"] not in {"completed", "failed"} for r in rows)
    # 지연값이 없는 요청을 0ms로 채우지 않아요. 알려진 완료 지연만 정렬해요.
    times = sorted(r["latency_ms"] for r in finished if r.get("latency_ms") is not None)
    # 실패한 요청도 과금될 수 있으므로 비용은 완료 여부로 거르지 않아요.
    # None은 미확인, 숫자 0은 확인된 무료 요청이라는 차이를 유지해요.
    costs = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
    # nearest-rank p95의 배열 위치는 ceil(0.95 × 표본 수) - 1이에요.
    # 전체 비용은 모든 요청의 비용이 있을 때만 확정하고, 아니면 None을 반환해요.
    return {
        "requests": len(rows),
        "completed": len(finished),
        "errors": errors,
        "unknown": unknown,
        "error_rate": errors / len(rows) if rows else None,
        "p50_ms": median(times) if times else None,
        "p95_ms": times[ceil(0.95 * len(times)) - 1] if times else None,
        "latency_count": len(times),
        "known_cost_usd": sum(costs) if costs else None,
        "cost_coverage": len(costs) / len(rows) if rows else None,
        "total_cost_usd": sum(costs) if rows and len(costs) == len(rows) else None,
    }
