# TIL 2026-10-30 · LLMOps : 실행 관측과 실패 원인 분석

> 한 줄 요약: **답변이 나온 뒤에 남은 증거(Trace)를 보고, 근거가 처음 사라진 단계를 찾는다.**
> completed ≠ 정답 · flush ≠ 서버 저장 · 자식 시간 합 ≠ 전체 시간 · 모르는 상태 ≠ 성공

---

## 1. 1-1 요청 단위 관측

### 같은 오답이라도 고칠 곳이 다르다

교육비 답변에서 "수료증"이 빠졌다면 원인은 세 가지 중 하나다.

| 관측한 증거 | 실패 위치 | 고칠 대상 |
|---|---|---|
| 검색 문서가 비어 있음 | 검색 | 키워드·검색 조건 |
| 문서는 찾았는데 모델 입력에 문장이 없음 | 입력 조립 | context 만드는 코드 |
| 입력엔 있는데 답에서 빠짐 | 생성 | 응답 지시·필수 사실 검사 |

→ 최종 답변만 보면 셋을 구분할 수 없다. **모델을 바꾸기 전에 근거가 처음 사라진 단계부터 찾는다.**

### 용어

- **Trace**: 요청 하나 전체를 묶는 단위
- **observation**: 그 안의 단계. `span`은 일반 작업 구간, `GENERATION`은 모델 호출 구간
- 트리의 노드 수 ≠ 모델 호출 수. `ChatPromptTemplate`은 메시지 구성일 뿐이고, 실제 호출은 `ChatOpenAI` 하나다.

### `answer()` 뼈대

기록 코드를 걷어내면 하는 일은 이게 전부다.

```python
docs = retrieve(question)                 # ① 검색
context = "[id] text" 형태로 합치기          # ② 입력 조립
reply = (prompt | model).invoke(...)      # ③ 생성
if 미완성: raise MODEL_RESPONSE_INCOMPLETE  # ④ 검증
return {answer, trace_id, ...}            # ⑤ 다음 강의로 넘길 데이터
```

**`with` 블록이 겹친 모양이 그대로 Langfuse 트리 모양이 된다.**

```
policy-qa (span)              ← with 바깥
 ├─ retrieve (span)           ← 수동 기록
 └─ generate-answer (chain)   ← CallbackHandler 자동 기록
     ├─ ChatPromptTemplate
     └─ ChatOpenAI (GENERATION)
```

### 오늘 알게 된 디테일

- `start_as_current_observation`의 **current**: 이 span을 "현재 활성 구간"으로 등록한다. 그래서 안쪽에서 만든 기록이 자동으로 자식이 된다.
- 일반 Python 함수(`retrieve`)는 자동 추적되지 않는다. 그래서 **수동 span**으로 감싼다.
- `CallbackHandler()`는 만들기만 해서는 기록되지 않는다. **`invoke(config={"callbacks": [handler]})`로 넘겨야** 작동한다.
- context에 `[training] 교육비는...`처럼 **ID를 함께** 넣는다. 그래야 답변의 출처를 검사할 수 있다.
- 지시는 `system`, 근거와 질문은 `human`으로 분리한다.
- `started`는 `datetime.now(timezone.utc)`로 **시간대가 붙은 UTC 시각**으로 기록한다 (1-2 조회와 1-4 판정에서 쓴다).
- `perf_counter()`는 시계가 아니라 **간격 측정 전용** 스톱워치다.
- `usage`가 없으면 `None`으로 둔다. **비용을 모른다 ≠ 비용이 0**
- `app_version`은 코드가 붙인 표지일 뿐이라 값만 바꾼다고 실행이 바뀌지 않는다. 실제 변경과 **함께** 바꿔야 한다.

### 호출 성공 ≠ 품질 성공

```python
if reply.response_metadata.get("status") != "completed" or not reply.text.strip():
    raise RuntimeError("MODEL_RESPONSE_INCOMPLETE")
```

- HTTP가 성공해도 답이 잘렸거나(출력 한도 초과) 비어 있으면 실패로 본다.
- 이걸 통과해도 "20만원·영수증·수료증"이 맞는지는 **모른다**. 내용 평가는 2장에서 한다.
- 실제 결과: `교육비는 연간 20만 원까지 지원되며, 영수증과 수료증이 필요합니다. [training]` → 체크리스트 통과

---

## 1. 1-2 Trace 재조회

### 세 단계는 서로 다르다

| 보이는 현상 | 알 수 있는 것 | 아직 모르는 것 |
|---|---|---|
| 터미널에 답변이 나옴 | 로컬이 응답을 받음 | Langfuse 저장 여부 |
| `flush()` 완료 | 남은 기록을 전송함 | 서버 검색 반영 여부 |
| 서버에서 GENERATION 조회됨 | 서버에 모델 실행 기록이 있음 | 답의 정답 여부 |

- 기록이 안 보인다고 **모델을 다시 부르지 않는다.** 비용이 들고 Trace가 하나 더 생긴다. **조회만** 다시 한다.

### 조회 코드

```python
row = read("result_01.json")
observations = lf.api.observations.get_many(
    trace_id=row["trace_id"],         # 질문 문장이 아니라 ID로 → 다른 실행과 섞이지 않음
    from_start_time=시작 - 1분,
    to_start_time=지금 + 1분,
    fields="core,basic,usage,model,io",
    limit=30,
).data
```

### 판정

```python
if not observations:
    raise ValueError(...)              # 0개 = "아직 모름" (저장 실패로 단정 X)
generations = [x for x in observations if x.type.upper() == "GENERATION"]
if not generations or any(x.end_time is None for x in generations):
    raise RuntimeError("GENERATION_NOT_CONFIRMED")
```

- retrieve span만 있는 건 모델 호출 완료의 증거가 아니다. **type이 GENERATION이고 `end_time`이 있어야** 한다.
- 반환 목록은 트리 순서가 아니다. name·type·부모 관계로 구조를 읽는다.
- 브라우저는 현지 시각, 결과 파일은 UTC로 보인다. **시각 말고 Trace ID로** 맞춘다.

---

## 1. 1-3 업무 도구 추적

### 출처마다 책임지는 사실이 다르다

| 출처 | 내용 | 의미 |
|---|---|---|
| travel (규정 문서) | 1박 10만원, 영수증 | 누구에게나 적용되는 한도 |
| approval (업무 조회) | REQ-DEMO-01, 승인, 8만원 | 이 요청 한 건의 상태 |

→ **8만원 승인 ≠ 숙박 한도 8만원**

### 코드 구조

```python
with lf.start_as_current_observation(name="qa-with-business-lookup", as_type="span") as request:
    with lf.start_as_current_observation(name="lookup-approval", as_type="tool",
                                         input={"request_id": "REQ-DEMO-01"}) as tool:
        approval = {...}               # 모의 DB
        tool.update(output=approval)
    row = answer(lf, model, "...", extra_context="\n[approval] 요청 REQ-DEMO-01: 승인, 8만원")
```

```
qa-with-business-lookup        ← Trace 루트
 ├─ lookup-approval (tool)
 └─ policy-qa                  ← 01에서는 루트였던 것이 자식이 됨
     ├─ retrieve
     └─ generate-answer → ChatOpenAI
```

### 오늘의 발견

- **같은 `answer()`인데 트리 위치가 바뀐다.** 활성 span이 없으면 새 Trace를 만들고, 있으면 그 아래 자식으로 붙는다. 함수를 고치지 않고 감싸기만 해도 구조가 합쳐진다.
  - 확인 방법: `print(row["trace_id"] == request.trace_id)` → `True`
- `as_type="tool"`은 **기록상 유형 표시**일 뿐이다. 실제 외부 도구를 호출했다는 뜻이 아니다.
- ⚠️ **실제 결과에서 찾은 함정**
  ```json
  "answer": "... 승인 금액은 8만 원입니다. [travel] [approval]",
  "document_ids": ["travel"]
  ```
  답변은 `[approval]`을 인용했지만 `document_ids`에는 travel만 있다. `document_ids`는 **`retrieve()` 결과만** 세고 `extra_context`는 세지 않기 때문이다.
  → 출처 검사를 `document_ids`로만 하면 `[approval]`이 "없는 출처"로 잘못 판정될 수 있다.
  → 승인 금액은 **lookup-approval의 출력**과 대조해야 한다.

### 부모 시간에 자식 시간이 포함된다

```
qa-with-business-lookup  1.5s
  ├ lookup-approval      0.1s
  └ policy-qa            1.3s
```

- ✗ 1.5 + 0.1 + 1.3 = 2.9초 → 중복 계산
- ✓ 사용자가 기다린 시간 = **바깥 구간 1.5초**, 병목은 policy-qa 안에서 찾는다.
- `result_03.json`의 `latency_ms`(5096ms)는 `answer()` 안에서 잰 **policy-qa 구간 시간**이다. 전체 시간이 아니다.

---

## 1. 1-4 실패 분류

### 판정 순서가 결과를 바꾼다

```python
def classify(row):
    if row.get("status") not in {"completed", "failed"}:
        return "incomplete"                       # ① 모르는 상태는 성공으로 추정 X
    try:
        start, end = [datetime.fromisoformat(row[k]) for k in ("started_at", "ended_at")]
        if start.tzinfo is None or end.tzinfo is None or end < start:
            return "invalid_time"                 # ② 시간대 없음·역전
    except (KeyError, TypeError, ValueError):     #    키 없음 / None / 형식 오류
        return "invalid_time"
    if row["status"] == "failed":
        return "model_error"                      # ③
    if not row.get("document_ids"):
        return "retrieval_empty"                  # ④ [] 와 None 모두 잡음
    return "completed"
```

- 먼저 검사한 조건이 **대표 분류**가 된다.
- `try`는 **파싱 부분만** 감싼다. 다른 버그까지 덮지 않게 하기 위해서다.
- 시간대가 없는 시각과 있는 시각을 비교하면 TypeError가 난다. 그래서 `tzinfo` 검사가 `end < start`보다 **앞에** 있다 (`or`는 앞에서 True면 뒤를 실행하지 않는다).
- 상태가 없는 행을 정상으로 세면 **성공률이 실제보다 높아 보인다.**

### 모의 사례 만들기

```python
cases = [("모델 실패", {**base, "status": "failed"}), ...]
```

- `{**base, 필드: 값}` = base를 복사하면서 **필드 하나만 바꾼다**. 결과가 달라진 원인이 그 필드라는 게 분명해진다.

| 사례 | 결과 |
|---|---|
| 정상 | completed |
| 모델 실패 | model_error |
| 검색 없음 | retrieval_empty |
| 상태 누락 | incomplete |
| 날짜 오류 | invalid_time |
| 시간 역전 | invalid_time |

### 점수는 같은 Trace에

```python
with lf.start_as_current_observation(name="simulated-failure-case", input=sample,
                                     metadata={"simulation": True}) as span:
    span.update(output=..., level="DEFAULT" if outcome == "completed" else "WARNING")
    lf.create_score(trace_id=span.trace_id, name="failure_category",
                    value=outcome, data_type="CATEGORICAL")
```

- 바깥에 활성 span이 없으니 **사례마다 새 Trace**가 생긴다 (trace_id 6개가 모두 다르다).
- 분류값만 따로 모으면 어떤 입력을 보고 판정했는지 알 수 없다. **입력이 담긴 Trace에 점수를 붙인다.**
- `simulation: True` → 운영 오류율의 **분모에서 빼기 위한 표시**
- Trace 단위 점수는 화면 **상단**에 있다. ChatOpenAI 노드의 Scores 탭에는 없다.

### 검색 없음 = 실패?

| 질문 | 기대 행동 | 판단 |
|---|---|---|
| 재택근무 지원금은? | 규정 밖이니 "확인할 수 없습니다" | 올바른 보류 |
| 교육비 증빙인데 표현 차이로 못 찾음 | training을 찾았어야 함 | 검색 결함 |

→ 둘 다 문서 목록은 비어 있지만 **같은 결함으로 묶으면 안 된다.** 기대 행동을 붙여야 판단할 수 있고, 이것이 2장 **Golden Dataset**으로 이어진다.

---

## 6. course.py 공통 부품 메모

### `connect()`

- `load_dotenv(HERE / ".env", encoding="utf-8-sig")`: 어디서 실행해도 이 장 폴더의 .env를 읽는다. `utf-8-sig`는 윈도우 메모장의 BOM을 무시한다.
- `LANGSMITH_TRACING=false`: 기록이 Langfuse에만 가게 한다.
- 키 4개가 비어 있으면 **모델을 부르기 전에** `ValueError`로 멈춘다.
- `Langfuse(environment="llmops-course", sample_rate=1.0)`: 화면 필터 이름, 모든 요청 기록
- `atexit.register(lf.shutdown)`: 종료할 때 남은 기록을 보내는 안전장치
- `ChatOpenAI` 옵션
  - `max_retries=0`: 실패를 숨기지 않고 중복 비용도 막는다
  - `max_tokens=400`: 넘으면 status가 completed가 아니게 된다
  - `use_responses_api=True`: **`status` 검사가 가능한 이유**
  - `store=False`: OpenAI 쪽에 대화를 저장하지 않는다

### `retrieve()`

```python
return [doc for doc in DOCUMENTS if any(word in question for word in doc["keywords"])]
```

일부러 단순한 키워드 검색이다. 관측에 집중하기 위해서다. "강의 수강료"처럼 키워드가 없는 표현을 쓰면 검색 실패 사례를 직접 만들어 볼 수 있다.

### `run()`

- API 에러 원문에는 키가 섞일 수 있어서 **종류 + HTTP 상태만** 출력한다.
- 수업 코드가 정한 에러(`safe_errors`)에는 해결 안내를 함께 출력한다.
- `SystemExit(1)`: 실패를 종료 코드로 남긴다. 다른 모델로 바꾸거나 성공 데이터로 대체하지 않는다.

### `finish()`

`lf.flush()`는 "남은 기록을 지금 보내라"는 뜻이다. 서버 반영 시점은 다를 수 있어서 02가 따로 있다.

---

## 2. 코드 전체에 흐르는 원칙

| 원칙 | 코드 |
|---|---|
| 돈 쓰기 전에 먼저 실패하기 | `missing` 검사, `auth_check()`, `max_retries=0` |
| 기록 구조 = `with` 중첩 구조 | `answer()`, 03의 바깥 span |
| 판정은 Python, 보관은 Langfuse | `create_score` |
| 결과 파일이 강의 사이의 바통 | `save`/`read`, `trace_id` |
| 모르는 걸 성공으로 채우지 않기 | `incomplete`, `usage=None`, exit 1 |
| 실패 원문은 숨기되 실패 자체는 숨기지 않기 | `run()`의 `safe_errors` |
