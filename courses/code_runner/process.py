import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from django.conf import settings


WINDOWS_ENV_PASSTHROUGH = (
    "ALLUSERSPROFILE",
    "CommonProgramFiles",
    "CommonProgramFiles(x86)",
    "CommonProgramW6432",
    "OS",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROCESSOR_IDENTIFIER",
    "PROCESSOR_LEVEL",
    "PROCESSOR_REVISION",
    "ProgramData",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "ProgramW6432",
)


def runner_settings():
    return getattr(settings, "CODE_RUNNER", {})


def max_output_chars():
    return int(runner_settings().get("MAX_OUTPUT_CHARS", 6000))


def compile_timeout_seconds():
    return int(runner_settings().get("COMPILE_TIMEOUT_SECONDS", 15))


def resolve_command(command):
    if not command:
        return None
    command_path = Path(str(command))
    if command_path.exists():
        return str(command_path)
    return shutil.which(str(command))


def minimal_env(workspace):
    runner_home = workspace / ".runner_home"
    roaming_appdata = runner_home / "AppData" / "Roaming"
    local_appdata = runner_home / "AppData" / "Local"
    nuget_packages = runner_home / ".nuget" / "packages"
    cache_dir = runner_home / ".cache"

    for path in (runner_home, roaming_appdata, local_appdata, nuget_packages, cache_dir):
        path.mkdir(parents=True, exist_ok=True)

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(runner_home),
        "TMP": str(workspace),
        "TEMP": str(workspace),
        "TMPDIR": str(workspace),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_GENERATE_ASPNET_CERTIFICATE": "0",
        "DOTNET_ADD_GLOBAL_TOOLS_TO_PATH": "0",
        "DOTNET_NOLOGO": "1",
        "DOTNET_DISABLE_GUI_ERRORS": "1",
        "DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE": "true",
        "DOTNET_SKIP_WORKLOAD_INTEGRITY_CHECK": "true",
        "DOTNET_CLI_HOME": str(runner_home),
        "NUGET_PACKAGES": str(nuget_packages),
        "USERPROFILE": str(runner_home),
        "APPDATA": str(roaming_appdata),
        "LOCALAPPDATA": str(local_appdata),
        "XDG_CACHE_HOME": str(cache_dir),
    }
    # Preserve key Windows installation paths so NuGet and workload discovery
    # can resolve machine-wide defaults inside the isolated runner environment.
    for key in ("SystemRoot", "WINDIR", "ComSpec", "DOTNET_ROOT", "DOTNET_ROOT(x86)", *WINDOWS_ENV_PASSTHROUGH):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


def run_command(command, workspace, timeout_seconds):
    start_time = time.monotonic()
    popen_kwargs = {
        "cwd": workspace,
        "env": minimal_env(workspace),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **popen_kwargs)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_process_tree(process)
        stdout, stderr = process.communicate()

    duration_ms = int((time.monotonic() - start_time) * 1000)
    return {
        "returncode": process.returncode,
        "stdout": truncate_output(stdout),
        "stderr": truncate_output(stderr),
        "duration_ms": duration_ms,
        "timed_out": timed_out,
    }


def kill_process_tree(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        process.kill()


def truncate_output(text):
    if text is None:
        return ""
    text = text.replace("\r\n", "\n")
    limit = max_output_chars()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}\n...[output truncated]..."
