# 2장: 평가 데이터와 변경 전후 검증

Windows의 VS Code에서 이 폴더를 열고 PowerShell 터미널을 사용하세요.

각 장의 폴더에 `.env`가 필요해요. 이 폴더의 `.env.example`을 `.env`로 복사한 뒤 본인의 OpenAI 키, Langfuse 프로젝트 키와 지역 주소를 입력하세요. `.env`가 있다면 덮어쓰지 마세요. `OPENAI_MODEL`은 비워 두면 `gpt-5.6-luna`를 사용해요.

```powershell
uv sync --locked
uv run --locked 01_dataset.py
uv run --locked 02_prompts.py
uv run --locked 03_evaluate.py
uv run --locked 04_compare.py
```

위 명령은 순서대로 한 줄씩 실행해요. uv가 프로젝트 환경을 관리하므로 가상환경 생성이나 활성화 명령은 필요 없어요.

## 파일 읽는 순서

- `01_dataset.py`: Golden Dataset 설계와 등록
- `02_prompts.py`: 프롬프트 버전과 비교 조건 고정
- `03_evaluate.py`: Python 평가와 Langfuse 실험 실행
- `04_compare.py`: 변경 전후 비교와 회귀 판정
- `course.py`: 같은 질의응답 흐름과 설정을 함께 쓰는 함수예요. 강의 파일에서 사용한 함수부터 읽으세요.
- `golden.json`, `evaluation.py`: 질문 6개와 두 버전에 공통으로 적용할 평가 규칙이에요.

실행 후 만들어지는 `result_*.json`에는 다음 강의에서 다시 읽을 결과가 담겨요. 원본 ZIP에는 결과 파일이 들어 있지 않아요. API 키가 담긴 `.env`와 자동 생성된 `.venv`는 공유하지 마세요.

## 다시 실행할 때

- `01_dataset.py`나 `02_prompts.py`를 다시 실행했다면 `03_evaluate.py`, `04_compare.py`도 순서대로 다시 실행하세요. 새 데이터셋이나 프롬프트에 맞는 평가 결과가 필요해요.
- `03_evaluate.py`를 다시 실행하면 실제 모델을 최대 8회 호출해요. 화면에 기록이 늦게 보이는 경우에는 먼저 기존 실험 화면을 다시 확인하세요.

실행 실패가 표시되면 다음 명령으로 넘어가지 마세요. 실패한 실행은 이전에 성공한 `result_*.json`을 지우지 않아요. 파일이 있다는 이유만으로 이번 실행이 성공했다고 판단하지 말고, 오류를 해결한 뒤 해당 명령이 정상 종료됐는지 확인하세요.

## 호출과 결과

- 1강: 모델 호출 없음. 데이터셋 등록
- 2강: 모델 호출 없음. 프롬프트 등록
- 3강: 실제 모델 8회. dev 4개 × 두 버전
- 4강: dev 통과 시 실제 모델 2회. 미통과 시 추가 호출 없음

조회 직후 기록이 안 보이면 모델 코드를 반복 호출하지 말고 잠시 뒤 조회 파일이나 Trace 화면을 다시 확인하세요. 실패는 종료 코드 1로 표시하고 숨기지 않아요. 답변 문장과 지연은 달라질 수 있어요.

## 강의 퀴즈

강의마다 퀴즈 파일 세 개가 있어요. 모델과 Langfuse를 호출하지 않아서 `.env` 없이도 실행돼요.

- `qN_hard.py`: TODO를 직접 완성해요.
- `qN_easy.py`: 빈칸(`____`)을 채워요. Hard가 막히면 이 파일로 풀어요.
- `qN_solution.py`: 정답 코드예요.

```powershell
uv run --locked q1_easy.py
```

N은 강의 번호예요(1강 → q1). 통과하면 `✅ 정답이에요!`와 생각해 볼 질문이 출력돼요.

2 · 3장 퀴즈는 진짜 수업 코드(`answer`, `experiment`, `summarize` 등)를 `quiz_lab.py`의 규칙 모델로 돌려요. 상황을 바꿔 보면서 코드가 어떻게 달라지는지 확인해요. 실제 LLM이 아니어서 답변 · 토큰 · 비용은 설명용이에요.
