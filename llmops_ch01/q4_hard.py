# -*- coding: utf-8 -*-
# 1장 4강 퀴즈: 취소된 요청을 새 분류로 추가해요 (Hard: TODO를 직접 완성해요)
# 이 폴더에서 uv run q4_hard.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

from datetime import datetime


# 사용자가 요청을 취소한 기록(cancelled)을 새 분류로 추가하세요. 기록 형식 검사가 먼저예요.
def classify(row):
    if row.get("status") not in {"completed", "failed", "cancelled"}:
        return "incomplete"
    try:
        start, end = [datetime.fromisoformat(row[k]) for k in ("started_at", "ended_at")]
        if start.tzinfo is None or end.tzinfo is None or end < start:
            return "invalid_time"
    except (KeyError, TypeError, ValueError):
        return "invalid_time"
    if row["status"] == "failed":
        return "model_error"
    if row["status"] == "cancelled":
        return "cancelled"
    if not row.get("document_ids"):
        return "retrieval_empty"
    return "completed"



# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
base = {
    "status": "completed",
    "started_at": "2026-01-01T00:00:00+00:00",
    "ended_at": "2026-01-01T00:00:01+00:00",
    "document_ids": ["meal"],
}
cases = [
    ("정상", base, "completed"),
    ("취소", {**base, "status": "cancelled"}, "cancelled"),
    ("취소 + 문서 없음", {**base, "status": "cancelled", "document_ids": []}, "cancelled"),
    ("취소 + 시간 역전", {**base, "status": "cancelled", "ended_at": "2025-12-31T23:59:59+00:00"}, "invalid_time"),
    ("모르는 상태", {**base, "status": "timeout"}, "incomplete"),
    ("시간대 없음", {**base, "ended_at": "2026-01-01T00:00:01"}, "invalid_time"),
    ("모델 실패", {**base, "status": "failed", "document_ids": []}, "model_error"),
]
for label, row, want in cases:
    got = classify(row)
    print(f"{label:<12} -> {got}")
    assert got == want, f"{label}: {want}이어야 해요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "취소된 요청은 오류율의 분모에 넣어야 할까요? 3장에서 운영 지표로 보고할 때 어떻게 표시할지 생각해 보세요.")
