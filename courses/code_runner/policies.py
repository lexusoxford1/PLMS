from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SourceRestriction:
    pattern: str
    explanation: str
    hint: str


RESTRICTIONS = {
    "python": [
        SourceRestriction(
            pattern=r"(^|\n)\s*(import|from)\s+(os|subprocess|socket|pathlib|shutil|ctypes|requests|urllib|http|tempfile|threading|multiprocessing)\b",
            explanation="This lesson runner blocks Python modules that can access the system or the network.",
            hint="Use beginner-friendly Python features such as variables, conditions, loops, functions, and print().",
        ),
        SourceRestriction(
            pattern=r"\b(open|exec|eval|compile|__import__|input|breakpoint)\s*\(",
            explanation="This lesson runner blocks Python functions that can open files, execute dynamic code, or wait for input.",
            hint="Write code that computes and prints the result directly without reading files or asking for keyboard input.",
        ),
    ],
    "php": [
        SourceRestriction(
            pattern=r"\b(exec|shell_exec|system|passthru|proc_open|popen|pcntl_exec|curl_exec|curl_init|file_get_contents|fopen|unlink|rename|mkdir|rmdir|scandir|opendir|eval|require|include)(_once)?\s*\(",
            explanation="This lesson runner blocks PHP functions that can access files, system commands, or external resources.",
            hint="Keep the solution focused on basic PHP syntax, variables, conditions, loops, arrays, functions, and echo.",
        ),
        SourceRestriction(
            pattern=r"`.+`|\$_(SERVER|ENV|FILES|COOKIE|SESSION|REQUEST|POST|GET)",
            explanation="This lesson runner blocks PHP features that expose server data or shell execution.",
            hint="Use plain PHP variables and output statements instead of server or shell features.",
        ),
    ],
    "csharp": [
        SourceRestriction(
            pattern=r"using\s+System\.(IO|Diagnostics|Net|Reflection|Runtime\.InteropServices|Threading)\s*;",
            explanation="This lesson runner blocks C# namespaces that can reach the file system, processes, networking, or low-level system APIs.",
            hint="Use core console-programming features such as Console, variables, loops, methods, arrays, and conditionals.",
        ),
        SourceRestriction(
            pattern=r"\b(File|Directory|Path|Process|Environment|Assembly|Activator|Marshal|DllImport|Console\.Read(Line|Key)?)\b",
            explanation="This lesson runner blocks C# APIs that can read files, start processes, inspect the environment, or wait for input.",
            hint="Print the answer directly and avoid file access, process access, or keyboard input.",
        ),
    ],
}


def find_blocked_construct(language, source):
    for restriction in RESTRICTIONS.get(language, []):
        if re.search(restriction.pattern, source or "", flags=re.IGNORECASE | re.MULTILINE | re.DOTALL):
            return restriction
    return None
