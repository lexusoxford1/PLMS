import sys
import tempfile
from pathlib import Path

from django.conf import settings

from courses.csharp_runner.compiler import compile_and_execute_csharp

from .process import resolve_command, run_command, runner_settings
from .schemas import CodeExecutionResult


SUPPORTED_LANGUAGES = {"python", "php", "csharp"}


def execute_code(language, source, *, timeout_seconds=None):
    if language not in SUPPORTED_LANGUAGES:
        return CodeExecutionResult(
            language=language,
            execution_status="error",
            errors=f"Unsupported language: {language}",
        )

    timeout_seconds = timeout_seconds or runner_settings().get("DEFAULT_TIMEOUT_SECONDS", 5)
    execution_root = Path(runner_settings().get("EXECUTION_ROOT", settings.BASE_DIR / ".code_runner"))
    execution_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=execution_root) as temp_dir:
        workspace = Path(temp_dir)
        if language == "python":
            return _execute_python(source, workspace, timeout_seconds)
        if language == "php":
            return _execute_php(source, workspace, timeout_seconds)
        return compile_and_execute_csharp(source, workspace, timeout_seconds)


def _execute_python(source, workspace, timeout_seconds):
    interpreter = resolve_command(runner_settings().get("PYTHON_CMD") or sys.executable)
    if not interpreter:
        return CodeExecutionResult(
            language="python",
            execution_status="error",
            runtime_available=False,
            errors="Python runtime not found.",
        )

    source_path = workspace / "main.py"
    source_path.write_text(source, encoding="utf-8")
    command_result = run_command([interpreter, "-I", source_path.name], workspace, timeout_seconds)
    return CodeExecutionResult(
        language="python",
        execution_status="success" if command_result["returncode"] == 0 and not command_result["timed_out"] else "error",
        program_output=command_result["stdout"],
        errors=command_result["stderr"],
        execution_time_ms=command_result["duration_ms"],
        timed_out=command_result["timed_out"],
        details={"returncode": command_result["returncode"]},
    )


def _execute_php(source, workspace, timeout_seconds):
    interpreter = resolve_command(runner_settings().get("PHP_CMD") or "php")
    if not interpreter:
        return CodeExecutionResult(
            language="php",
            execution_status="error",
            runtime_available=False,
            errors="PHP CLI runtime not found.",
        )

    php_source = source if source.lstrip().startswith("<?php") else f"<?php\n{source}"
    source_path = workspace / "main.php"
    source_path.write_text(php_source, encoding="utf-8")
    command = [
        interpreter,
        "-n",
        "-d",
        f"open_basedir={workspace}",
        "-d",
        "disable_functions=exec,shell_exec,system,passthru,proc_open,popen,pcntl_exec,putenv,mail",
        source_path.name,
    ]
    command_result = run_command(command, workspace, timeout_seconds)
    return CodeExecutionResult(
        language="php",
        execution_status="success" if command_result["returncode"] == 0 and not command_result["timed_out"] else "error",
        program_output=command_result["stdout"],
        errors=command_result["stderr"],
        execution_time_ms=command_result["duration_ms"],
        timed_out=command_result["timed_out"],
        details={"returncode": command_result["returncode"]},
    )
