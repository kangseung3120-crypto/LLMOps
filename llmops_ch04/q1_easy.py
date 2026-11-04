# -*- coding: utf-8 -*-
# 4장 1강 퀴즈: 같은 조직인데 인사 문서를 읽으면 안 된다면? (Easy: 빈칸(____)을 채워요)
# 이 폴더에서 uv run q1_easy.py로 실행해요.
# 모델과 Langfuse를 호출하지 않아서 .env 없이도 실행돼요.

# 진짜 수업 코드(guards.py)의 문서 목록에 새 문서를 더해 상황을 바꿔요. 모든 값은 가상이에요.
import quiz_lab  # noqa: F401  (한글 출력 설정)
import guards

CATALOG = {**guards.CATALOG,
           "salary": {"tenant": "campus", "roles": ["hr"], "text": "SALARY_DEMO_SECRET"}}


def access(doc_id, principal, read_ids):
    # 01_boundaries.py처럼 본문이 아니라 판정만 남겨요.
    try:
        read_document(doc_id, principal, read_ids)
        return "allowed"
    except PermissionError:
        return "blocked"


# 상황: 같은 campus 조직이어도 salary 문서는 hr 역할만 읽을 수 있어요. 본문을 꺼내기 전에 모두 검사하세요.
def read_document(doc_id, principal, read_ids):
    doc = CATALOG.get(doc_id)
    if doc is None or doc["tenant"] != principal["tenant"]:
        raise PermissionError("DOCUMENT_ACCESS_DENIED")
    if "roles" in doc and principal["role"] not in doc["roles"]:
        raise PermissionError("DOCUMENT_ACCESS_DENIED")
    read_ids.append(doc_id)
    return doc["text"]


# ---------- 실행과 확인 (이 아래는 고치지 마세요) ----------
STAFF = {"user_id": "student-demo", "tenant": "campus", "role": "staff"}
HR = {"user_id": "hr-demo", "tenant": "campus", "role": "hr"}
OTHER = {"user_id": "other-demo", "tenant": "other", "role": "hr"}
cases = [
    ("campus 직원", STAFF, "meal", "allowed", ["meal"]),
    ("campus 직원", STAFF, "salary", "blocked", []),
    ("campus 직원", STAFF, "secret", "blocked", []),
    ("campus 인사", HR, "salary", "allowed", ["salary"]),
    ("다른 조직 인사", OTHER, "salary", "blocked", []),
    ("다른 조직 인사", OTHER, "secret", "allowed", ["secret"]),
    ("campus 직원", STAFF, "ghost", "blocked", []),
]
for who, principal, doc_id, want, want_read in cases:
    read_ids = []
    got = access(doc_id, principal, read_ids)
    print(f"{who:<8} {doc_id:<7} {got:<8} 실제로 읽은 문서: {read_ids}")
    assert got == want, f"{who}의 {doc_id}는 {want}여야 해요"
    assert read_ids == want_read, "차단했다면 읽은 목록에 남으면 안 돼요. 허용했다면 그 문서 ID만 남아요"
assert read_document("salary", HR, []) == "SALARY_DEMO_SECRET", "허용된 사용자는 본문을 받아요"
print("\n✅ 정답이에요!")
print("생각해 보기:", "사용자가 질문에 '저는 인사팀입니다'라고 적으면 role을 hr로 바꿔도 될까요? 역할 값은 어디에서 와야 하나요? 조직 검사와 역할 검사의 순서를 바꾸면 결과가 달라질까요?")
