import textwrap
from pathlib import Path

from courses.code_runner.process import compile_timeout_seconds, resolve_command, run_command, runner_settings
from courses.code_runner.schemas import CodeExecutionResult


def compile_and_execute_csharp(source, workspace, timeout_seconds):
    dotnet = resolve_command(runner_settings().get("DOTNET_CMD") or "dotnet")
    if not dotnet:
        return CodeExecutionResult(
            language="csharp",
            execution_status="error",
            runtime_available=False,
            errors=".NET CLI runtime not found.",
            details={"stage": "compile"},
        )

    project_name = "LessonRunner"
    framework = runner_settings().get("CSHARP_TARGET_FRAMEWORK", "net8.0")
    project_path = workspace / f"{project_name}.csproj"
    nuget_config_path = workspace / "NuGet.Config"
    source_path = workspace / "Program.cs"
    output_dir = workspace / "out"

    try:
        # Build each submission inside a one-off console project so the compiler
        # stays scoped to the current lesson workspace.
        project_path.write_text(
            textwrap.dedent(
                f"""
                <Project Sdk="Microsoft.NET.Sdk">
                  <PropertyGroup>
                    <OutputType>Exe</OutputType>
                    <TargetFramework>{framework}</TargetFramework>
                    <ImplicitUsings>enable</ImplicitUsings>
                    <Nullable>disable</Nullable>
                  </PropertyGroup>
                </Project>
                """
            ).strip(),
            encoding="utf-8",
        )
        nuget_config_path.write_text(
            textwrap.dedent(
                """
                <?xml version="1.0" encoding="utf-8"?>
                <configuration>
                  <packageSources>
                    <clear />
                  </packageSources>
                </configuration>
                """
            ).strip(),
            encoding="utf-8",
        )
        source_path.write_text(source, encoding="utf-8")

        restore_result = run_command(
            [
                dotnet,
                "restore",
                project_path.name,
                "--nologo",
                "--verbosity",
                "quiet",
                "--configfile",
                nuget_config_path.name,
                "--disable-build-servers",
                "-p:RestoreIgnoreFailedSources=true",
            ],
            workspace,
            compile_timeout_seconds(),
        )
        if restore_result["returncode"] != 0 or restore_result["timed_out"]:
            return _compile_failure_result(
                stage="restore",
                command_result=restore_result,
                compile_output=restore_result["stdout"],
            )

        build_result = run_command(
            [
                dotnet,
                "build",
                project_path.name,
                "--nologo",
                "--verbosity",
                "quiet",
                "--output",
                output_dir.name,
                "--no-restore",
                "--disable-build-servers",
            ],
            workspace,
            compile_timeout_seconds(),
        )
        if build_result["returncode"] != 0 or build_result["timed_out"]:
            return _compile_failure_result(
                stage="build",
                command_result=build_result,
                compile_output=_merge_output(restore_result["stdout"], build_result["stdout"]),
                duration_ms=restore_result["duration_ms"] + build_result["duration_ms"],
            )

        dll_path = output_dir / f"{project_name}.dll"
        run_result = run_command([dotnet, str(dll_path)], workspace, timeout_seconds)
        runtime_errors = _merge_output(run_result["stderr"], run_result["stdout"] if run_result["returncode"] else "")
        return CodeExecutionResult(
            language="csharp",
            execution_status="success" if run_result["returncode"] == 0 and not run_result["timed_out"] else "error",
            program_output=run_result["stdout"],
            errors=runtime_errors,
            compile_output=_merge_output(restore_result["stdout"], build_result["stdout"]),
            execution_time_ms=restore_result["duration_ms"] + build_result["duration_ms"] + run_result["duration_ms"],
            timed_out=run_result["timed_out"],
            details={
                "returncode": run_result["returncode"],
                "stage": "runtime" if run_result["returncode"] else "execute",
                "files": ["Program.cs"],
            },
        )
    except OSError as exc:
        return _exception_failure_result(exc)
    except Exception as exc:
        return _exception_failure_result(exc)


def _merge_output(*parts):
    return "\n".join(part for part in parts if part).strip()


def _compile_failure_result(*, stage, command_result, compile_output="", duration_ms=None):
    compile_errors = _merge_output(command_result["stderr"], command_result["stdout"])
    return CodeExecutionResult(
        language="csharp",
        execution_status="error",
        errors=compile_errors,
        compile_output=compile_output,
        compile_errors=compile_errors,
        execution_time_ms=duration_ms if duration_ms is not None else command_result["duration_ms"],
        timed_out=command_result["timed_out"],
        details={
            "returncode": command_result["returncode"],
            "stage": "compile",
            "compiler_stage": stage,
            "environment_issue": _detect_environment_issue(compile_errors),
            "files": ["Program.cs"],
        },
    )


def _exception_failure_result(exc):
    message = f"The lesson compiler hit an unexpected setup problem: {exc}"
    return CodeExecutionResult(
        language="csharp",
        execution_status="error",
        errors=message,
        compile_errors=message,
        details={
            "stage": "compile",
            "compiler_stage": "prepare",
            "environment_issue": "compiler_service_exception",
            "files": ["Program.cs"],
        },
    )


def _detect_environment_issue(errors):
    checks = (
        (
            "workload_verification",
            (
                "verifying workloads",
                "NuGet.Configuration.ConfigurationDefaults",
                "Value cannot be null. (Parameter 'path1')",
            ),
        ),
        (
            "nuget_configuration",
            (
                "Failed to read NuGet.Config",
                "NuGet.Config",
                "UnauthorizedAccessException",
            ),
        ),
        (
            "msbuild_environment",
            (
                "MSBuildTemp",
                "internal failure occurred while running MSBuild",
            ),
        ),
    )
    haystack = errors or ""
    for issue_code, markers in checks:
        if any(marker.lower() in haystack.lower() for marker in markers):
            return issue_code
    return ""
