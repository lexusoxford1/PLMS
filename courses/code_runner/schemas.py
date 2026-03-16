from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeExecutionResult:
    language: str
    execution_status: str
    program_output: str = ""
    errors: str = ""
    execution_time_ms: int = 0
    runtime_available: bool = True
    timed_out: bool = False
    compile_output: str = ""
    compile_errors: str = ""
    details: dict[str, Any] = field(default_factory=dict)
