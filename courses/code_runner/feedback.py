import re


LANGUAGE_LABELS = {
    "python": "Python",
    "php": "PHP",
    "csharp": "C#",
}


def language_label(language):
    return LANGUAGE_LABELS.get(language, language.upper())


def build_beginner_friendly_error(language, errors, *, timed_out=False, runtime_available=True):
    if not runtime_available:
        label = language_label(language)
        return (
            f"The {label} runtime is not available on this server yet, so your code could not be checked.",
            f"Ask your instructor or administrator to install and configure the {label} runtime.",
            "While waiting, review the lesson example and keep your solution ready to test again.",
        )

    if timed_out:
        return (
            "Your program took too long to finish, so it was stopped for safety.",
            "Check for loops that never end or code that is waiting for input.",
            "Trace the program step by step and confirm every loop moves toward a stopping condition.",
        )

    patterns = {
        "python": [
            (
                r"SyntaxError|IndentationError",
                "Python found a syntax problem before the program could run.",
                "Check punctuation, parentheses, colons, and indentation near the line mentioned in the error.",
            ),
            (
                r"NameError",
                "Your program is using a name that Python does not recognize yet.",
                "Make sure each variable or function is spelled correctly and created before you use it.",
            ),
            (
                r"TypeError",
                "Python ran into a value type mismatch while executing your code.",
                "Check whether you are combining strings, numbers, or other values in the right way.",
            ),
            (
                r"ZeroDivisionError",
                "Your program tried to divide by zero while running.",
                "Change the value being used as a divisor or add a condition before dividing.",
            ),
        ],
        "php": [
            (
                r"Parse error|syntax error",
                "PHP found a syntax problem before the script could run.",
                "Check semicolons, parentheses, braces, and PHP opening tags near the reported line.",
            ),
            (
                r"Undefined variable",
                "Your script is using a variable that PHP has not been given a value yet.",
                "Create the variable first and make sure the name matches exactly, including the dollar sign.",
            ),
            (
                r"Call to undefined function",
                "PHP tried to call a function that does not exist in your code.",
                "Check the function name carefully and confirm it is defined before you call it.",
            ),
        ],
        "csharp": [
            (
                r"verifying workloads|ConfigurationDefaults|Value cannot be null\. \(Parameter 'path1'\)",
                "The lesson compiler ran into a .NET workload setup problem before it could check your code.",
                "This usually means the C# compiler environment needs attention, not your program logic.",
                "Try running the lesson again in a moment. If the same message returns, ask an administrator to verify the .NET workload and NuGet setup.",
            ),
            (
                r"Failed to read NuGet\.Config|UnauthorizedAccessException|MSBuildTemp",
                "The lesson compiler could not access part of its .NET or NuGet configuration.",
                "This is a compiler environment issue, so your C# code may not be the cause of the failure.",
                "Retry after the compiler service refreshes. If it keeps failing, ask an administrator to check the runner permissions and NuGet configuration.",
            ),
            (
                r"error CS0103.*Console|The name 'Console' does not exist in the current context",
                "C# cannot find Console in your current program yet.",
                "Add using System; at the top of the file, or call System.Console.WriteLine(...) explicitly.",
            ),
            (
                r"error CS1002|; expected",
                "The C# compiler expected a semicolon and could not finish building your program.",
                "Review the line mentioned in the compiler output and make sure each statement ends with a semicolon.",
            ),
            (
                r"error CS1513|} expected",
                "The C# compiler found a missing closing brace.",
                "Match every opening brace with a closing brace, especially around methods and if statements.",
            ),
            (
                r"error CS0103",
                "Your program is using a name that C# cannot find in the current scope.",
                "Check spelling and make sure the variable or method is declared before it is used.",
            ),
            (
                r"NullReferenceException",
                "Your program tried to use an object that does not have a value yet.",
                "Create the object first or make sure it is assigned before you call its members.",
            ),
            (
                r"DivideByZeroException",
                "Your C# program tried to divide by zero while running.",
                "Update the divisor value or check it before dividing.",
            ),
        ],
    }

    for rule in patterns.get(language, []):
        pattern, explanation, hint = rule[:3]
        if re.search(pattern, errors or "", flags=re.IGNORECASE):
            suggestion = (
                rule[3]
                if len(rule) > 3
                else "Compare your code with the lesson example and fix one issue at a time, then run it again."
            )
            return (
                explanation,
                hint,
                suggestion,
            )

    return (
        f"Your {language_label(language)} code could not finish successfully.",
        "Read the error message, then compare it with your code around the line it mentions.",
        "Try a smaller version of the program first, then rebuild the final solution gradually.",
    )
