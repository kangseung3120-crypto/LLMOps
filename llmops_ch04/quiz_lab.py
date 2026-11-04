"""퀴즈 실습실: 실제 수업 코드를 API 키 없이 돌리기 위한 가짜 Langfuse와 규칙 모델이에요.

answer(), experiment(), evaluate(), compare(), summarize()는 진짜 수업 코드를 그대로 써요.
가짜인 것은 바깥 서비스 두 개뿐이에요.
- FakeLf: 기록을 서버로 보내지 않고 메모리에 담아요. 네트워크를 쓰지 않아요.
- RuleModel: 실제 LLM이 아니라 정해진 규칙으로 답해요. 같은 입력이면 항상 같은 답이 나와요.
토큰과 비용도 설명용 값이에요. 실제 모델의 수치나 행동을 뜻하지 않아요.
"""
import contextlib
import importlib
import io
import os
import re
import sys
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.callbacks import BaseCallbackHandler  # noqa: E402
from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402
from langchain_core.outputs import ChatGeneration, ChatResult  # noqa: E402

import course  # noqa: E402

PRICE_PER_TOKEN = 0.000001  # 설명용 단가예요.


class _Handler(BaseCallbackHandler):
    """Langfuse에 보내지 않는 빈 콜백이에요. answer()의 CallbackHandler() 자리에 들어가요."""


course.CallbackHandler = _Handler


class FakeLf:
    """수업 코드가 쓰는 Langfuse 메서드만 메모리로 흉내 내요."""

    def __init__(self):
        self.observations, self.scores, self.prompts, self.datasets = [], {}, {}, {}
        self._stack = []
        self.api = SimpleNamespace(observations=SimpleNamespace(get_many=self._get_many))

    @contextlib.contextmanager
    def start_as_current_observation(self, *, name, as_type="span", input=None, metadata=None, **_):
        trace_id = self._stack[0] if self._stack else uuid4().hex
        self._stack.append(trace_id)
        span = SimpleNamespace(trace_id=trace_id, id=uuid4().hex, update=lambda **kw: None)
        # 부모 span에도 비용 값이 보이는 상황을 만들어요. 함께 더하면 중복이에요.
        self.observations.append(SimpleNamespace(trace_id=trace_id, name=name, type=as_type.upper(), total_cost=0.0009))
        try:
            yield span
        finally:
            self._stack.pop()

    def record_generation(self, cost):
        self.observations.append(SimpleNamespace(trace_id=self._stack[0], name="ChatOpenAI", type="GENERATION", total_cost=cost))

    def _get_many(self, *, trace_id, **_):
        return SimpleNamespace(data=[o for o in self.observations if o.trace_id == trace_id])

    def create_score(self, *, trace_id, name, value, data_type=None, comment=None, score_id=None, **_):
        # 같은 score_id로 다시 보내면 새 점수가 아니라 기존 점수를 갱신해요.
        key = score_id or uuid4().hex
        self.scores[key] = {"trace_id": trace_id, "name": name, "value": value, "comment": comment}

    def scores_named(self, name):
        return [s for s in self.scores.values() if s["name"] == name]

    def create_prompt(self, *, name, prompt, type="text", **_):
        versions = self.prompts.setdefault(name, [])
        versions.append(SimpleNamespace(name=name, version=len(versions) + 1, prompt=prompt))
        return versions[-1]

    def get_prompt(self, name, *, version=None, label=None, cache_ttl_seconds=None):
        if version is not None and label is not None:
            raise ValueError("version과 label은 함께 지정할 수 없어요.")
        versions = self.prompts[name]
        if version is not None:
            return versions[version - 1]
        if label == "latest":
            return versions[-1]
        # 실제 SDK도 둘 다 없으면 production을 찾아요. 수업에서는 그 라벨을 달지 않아요.
        raise LookupError(f"{label or 'production'} 라벨이 붙은 버전이 없어요.")

    def create_dataset(self, *, name, description=None, **_):
        self.datasets[name] = FakeDataset(self, name)

    def create_dataset_item(self, *, dataset_name, input, expected_output, metadata=None, **_):
        self.datasets[dataset_name].items.append(
            SimpleNamespace(input=input, expected_output=expected_output, metadata=metadata))

    def get_dataset(self, name):
        return self.datasets[name]

    def flush(self):
        pass

    def get_trace_url(self, *, trace_id):
        return f"(가짜 주소) {trace_id}"


class FakeDataset:
    def __init__(self, lf, name):
        self.lf, self.name, self.items = lf, name, []

    def run_experiment(self, *, name, task, evaluators, max_concurrency=1, metadata=None):
        """실제 SDK 4.17의 실패 처리와 같아요. Task 예외는 행이 빠지고, 평가기 예외는 점수만 빠져요."""
        results = []
        for item in self.items:
            try:
                with self.lf.start_as_current_observation(name="experiment-item-task") as span:
                    output = task(item=item)
            except Exception:
                continue
            evaluations = []
            for evaluator in evaluators:
                with contextlib.suppress(Exception):
                    evaluations.extend(evaluator(input=item.input, output=output,
                                                 expected_output=item.expected_output, metadata=item.metadata))
            results.append(SimpleNamespace(item=item, output=output, evaluations=evaluations, trace_id=span.trace_id))
        # 반환 순서는 입력 순서와 다를 수 있어요. 그 상황을 보여 주려고 뒤집어요.
        return SimpleNamespace(item_results=results[::-1], dataset_run_url=f"(가짜 주소) {name}")


class RuleModel(BaseChatModel):
    """정해진 규칙으로 답하는 가짜 모델이에요. 실제 LLM의 행동을 예측하지 않아요."""

    model_name: str = "rule-model"
    lf: Any = None
    fail_on: tuple = ()        # 질문에 이 단어가 있으면 API 오류를 내요.
    incomplete_on: tuple = ()  # 질문에 이 단어가 있으면 응답이 잘려요.
    priced: bool = True        # False면 서버가 가격을 몰라 비용이 None이에요.

    @property
    def _llm_type(self):
        return "rule-model"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        instruction, human = messages[0].content, messages[-1].content
        question = human.rsplit("질문: ", 1)[-1]
        if any(word in question for word in self.fail_on):
            raise ConnectionError("가짜 API 오류")
        lines = dict(re.findall(r"^\[(\w+)\] (.+)$", human, flags=re.M))
        strict = "제공된 근거로만" in instruction
        if not lines:
            # '[meal]처럼 붙이세요'라는 예시가 있으면 보류 답변에도 그대로 복사해요 (2-4 교안의 실패 사례).
            text = "확인할 수 없습니다." + (" [meal]" if "처럼" in instruction else "")
        else:
            text = " ".join(lines.values()) + (" " + "".join(f"[{i}]" for i in lines) if strict else "")
        status = "incomplete" if any(word in question for word in self.incomplete_on) else "completed"
        usage = {"input_tokens": len(instruction + human) // 3, "output_tokens": len(text) // 3}
        usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
        if self.lf is not None:
            cost = usage["total_tokens"] * PRICE_PER_TOKEN if self.priced else None
            self.lf.record_generation(cost)
        message = AIMessage(content=text, usage_metadata=usage, response_metadata={"status": status})
        return ChatResult(generations=[ChatGeneration(message=message)])


def setup(**options):
    """연결된 가짜 Langfuse와 규칙 모델을 함께 만들어요."""
    lf = FakeLf()
    return lf, RuleModel(lf=lf, **options)


def lesson(name):
    """숫자로 시작하는 수업 파일을 가져와요. main()은 실행되지 않아요."""
    return importlib.import_module(name)


def dataset_from(lf, rows, name="quiz-dev"):
    """golden.json 행을 01_dataset.py와 같은 모양으로 등록해요."""
    lf.create_dataset(name=name)
    for row in rows:
        lf.create_dataset_item(dataset_name=name, input={"id": row["id"], "question": row["question"]},
                               expected_output=row["expected"], metadata={"split": row["split"], "kind": row["kind"]})
    return lf.get_dataset(name)


def quiet(fn, *args, **kwargs):
    """수업 코드의 print를 잠시 숨겨요. 고정 문구가 바뀐 상황과 달라 보일 때 써요."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)
