from dataclasses import asdict, dataclass, field
from typing import Any


SUCCESS_MESSAGE = "Correct answer. You have successfully completed this activity."
ERROR_MESSAGE = "Incorrect answer. Please review the lesson and try again."


@dataclass
class ActivityEvaluationResult:
    is_correct: bool
    title: str
    explanation: str
    execution_status: str = "success"
    program_output: str = ""
    errors: str = ""
    hint: str = ""
    learning_suggestion: str = ""
    language: str = ""
    execution_time_ms: int = 0
    runtime_available: bool = True
    timed_out: bool = False
    used_code_runner: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    notification: dict[str, Any] = field(default_factory=dict)

    @property
    def detail(self):
        return self.explanation

    @property
    def validation_result(self):
        return "correct" if self.is_correct else "incorrect"

    def to_payload(self):
        payload = asdict(self)
        payload["validation_result"] = self.validation_result
        return payload
