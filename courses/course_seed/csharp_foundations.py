from courses.models import Course

from .builders import (
    build_activity_content,
    build_code_activity_validation,
    build_lesson_content,
    required_pattern,
)


CSHARP_FOUNDATIONS = {
    "title": "C# Programming Foundations",
    "slug": "csharp-programming-foundations",
    "description": (
        "Build a strong start in C# with progressive lessons on syntax, variables, conditions, loops, methods, collections, and problem-solving."
    ),
    "overview": (
        "After completing this course, the learner will be able to write simple C# console programs, "
        "use core control structures, and organize beginner-level solutions using methods and collections."
    ),
    "difficulty": Course.BEGINNER,
    "estimated_hours": 10,
    "lessons": [
        {
            "title": "Getting Started with C#",
            "slug": "getting-started-with-csharp",
            "summary": "Understand the structure of a C# console program and display output.",
            "lecture_content": build_lesson_content(
                [
                    "C# is a modern programming language used for desktop apps, web apps, games, and enterprise systems.",
                    "A console application is a great place to begin because it helps you focus on core programming logic without interface complexity.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        Console.WriteLine("Hello, C# learner!");
                        Console.WriteLine("Welcome to programming foundations.");
                    }
                }
                """,
                [
                    "using System gives access to common classes like Console.",
                    "Main is the entry point of a console program.",
                    "Console.WriteLine displays output and moves to the next line.",
                ],
            ),
            "activity_title": "Activity 1: Console Introduction",
            "activity_instructions": build_activity_content(
                "Write a short C# console program that introduces the learner.",
                [
                    "Print your name on one line.",
                    "Print I am learning C# on the next line.",
                    "Print one more motivational message.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        // Write your Console.WriteLine statements here
                    }
                }
                """,
            ),
            "activity_hint": "Each Console.WriteLine call prints one full line.",
            "activity_validation": build_code_activity_validation(
                "csharp",
                expected_output=None,
                success_explanation=(
                    "Your answer is correct because it compiles and uses Console.WriteLine multiple times to produce clear console output."
                ),
                failure_hint=(
                    "Use at least three Console.WriteLine statements and include a line about C# or learning."
                ),
                starter_code="""
                using System;

                class Program
                {
                    static void Main()
                    {
                        // Write your Console.WriteLine statements here
                    }
                }
                """,
                required_patterns=[
                    required_pattern(r"Console\.WriteLine\s*\(", "three Console.WriteLine statements", count=3),
                    required_pattern(r"(C#|learning)", "a message about C# or learning"),
                ],
                min_output_lines=3,
                learning_suggestion="Try changing one printed line and run the compiler again to see how the output changes.",
            ),
        },
        {
            "title": "Variables and Data Types",
            "slug": "csharp-variables-and-data-types",
            "summary": "Declare variables and use strings, integers, doubles, and booleans.",
            "lecture_content": build_lesson_content(
                [
                    "Variables store data that your program can read and update.",
                    "C# is strongly typed, so each variable is declared with a data type such as string, int, double, or bool.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        string studentName = "Carlo";
                        int age = 18;
                        double average = 92.5;
                        bool isEnrolled = true;

                        Console.WriteLine(studentName);
                        Console.WriteLine(age);
                        Console.WriteLine(average);
                        Console.WriteLine(isEnrolled);
                    }
                }
                """,
                [
                    "string stores text, int stores whole numbers, double stores decimals, and bool stores true or false.",
                    "A variable declaration usually includes a type, a name, and an assigned value.",
                    "Strong typing helps catch mistakes early.",
                ],
            ),
            "activity_title": "Activity 2: Student Information Program",
            "activity_instructions": build_activity_content(
                "Create variables that describe a learner and display them.",
                [
                    "Declare a string variable for name.",
                    "Declare an int variable for age.",
                    "Declare a bool variable for whether the learner is ready.",
                    "Print all values using Console.WriteLine.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        string name = "";
                        int age = 0;
                        bool isReady = false;
                    }
                }
                """,
            ),
            "activity_hint": "Remember to end each C# statement with a semicolon.",
            "activity_validation": build_code_activity_validation(
                "csharp",
                expected_output=None,
                success_explanation=(
                    "This is correct because it declares the expected C# variables, compiles successfully, and outputs them using Console.WriteLine."
                ),
                failure_hint=(
                    "Declare string name, int age, and bool isReady, then print them with Console.WriteLine."
                ),
                starter_code="""
                using System;

                class Program
                {
                    static void Main()
                    {
                        string name = "";
                        int age = 0;
                        bool isReady = false;
                    }
                }
                """,
                required_patterns=[
                    required_pattern(r"\bstring\s+name\b", "a string name variable"),
                    required_pattern(r"\bint\s+age\b", "an int age variable"),
                    required_pattern(r"\bbool\s+isReady\b", "a bool isReady variable"),
                    required_pattern(r"Console\.WriteLine\s*\(", "a Console.WriteLine statement"),
                ],
                min_output_lines=3,
                learning_suggestion="After it compiles, try renaming one variable to see how strongly typed C# reacts to mismatches.",
            ),
        },
        {
            "title": "Conditional Statements",
            "slug": "csharp-conditional-statements",
            "summary": "Make decisions using if, else if, and else.",
            "lecture_content": build_lesson_content(
                [
                    "Programs make decisions by checking conditions that evaluate to true or false.",
                    "In C#, conditional statements let you choose which block of code should run in a given situation.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        int score = 84;

                        if (score >= 90)
                        {
                            Console.WriteLine("Excellent");
                        }
                        else if (score >= 75)
                        {
                            Console.WriteLine("Passed");
                        }
                        else
                        {
                            Console.WriteLine("Needs improvement");
                        }
                    }
                }
                """,
                [
                    "if checks the first condition.",
                    "else if checks another condition when needed.",
                    "else handles the remaining case.",
                ],
            ),
            "activity_title": "Activity 3: Result Evaluator",
            "activity_instructions": build_activity_content(
                "Write a program that checks whether a learner passed.",
                [
                    "Declare an int score variable.",
                    "If the score is 75 or higher, print Passed.",
                    "Otherwise, print Study and try again.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        int score = 0;
                    }
                }
                """,
            ),
            "activity_hint": "Conditions in C# are wrapped in parentheses.",
            "activity_validation": build_code_activity_validation(
                "csharp",
                expected_output=None,
                success_explanation=(
                    "Your solution is correct because it compiles and uses conditional logic to separate passing and non-passing outcomes."
                ),
                failure_hint=(
                    "Use an if statement with score >= 75 and include both a pass message and a retry message."
                ),
                starter_code="""
                using System;

                class Program
                {
                    static void Main()
                    {
                        int score = 0;
                    }
                }
                """,
                required_patterns=[
                    required_pattern(r"\bif\s*\(", "an if statement"),
                    required_pattern(r"score\s*>=\s*75", "a condition that checks score >= 75"),
                    required_pattern(r"Passed", "a passed output"),
                    required_pattern(r"(Study|try again)", "a retry message"),
                ],
                min_output_lines=1,
                concept_review={
                    "title": "Concept Review",
                    "badge": "Unlocked after success",
                    "summary": "Conditional logic helps a program choose between different outcomes.",
                    "body": (
                        "This activity uses an if/else decision. The condition score >= 75 checks whether the "
                        "learner passed. If that condition is true, the program prints Passed. Otherwise, the else "
                        "block runs and prints Study and try again."
                    ),
                },
                learning_suggestion="Trace which branch should run for the score value you chose before running the compiler again.",
            ),
        },
        {
            "title": "Loops and Repetition",
            "slug": "csharp-loops-and-repetition",
            "summary": "Repeat tasks with for and while loops.",
            "lecture_content": build_lesson_content(
                [
                    "Loops allow a program to repeat instructions efficiently instead of copying the same code many times.",
                    "A for loop is useful for counting, while a while loop is helpful when repetition depends on a changing condition.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        for (int i = 1; i <= 5; i++)
                        {
                            Console.WriteLine("Practice round " + i);
                        }

                        int countdown = 3;
                        while (countdown > 0)
                        {
                            Console.WriteLine(countdown);
                            countdown--;
                        }
                    }
                }
                """,
                [
                    "for loops combine start, condition, and update.",
                    "while loops continue as long as the condition remains true.",
                    "Loops are useful for counters, repeated messages, and list processing.",
                ],
            ),
            "activity_title": "Activity 4: Daily Practice Loop",
            "activity_instructions": build_activity_content(
                "Use a loop to simulate daily programming practice.",
                [
                    "Create a for loop from 1 to 5.",
                    "Inside the loop, print Practice day followed by the number.",
                    "After the loop, print Keep going.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        // Write your loop here
                    }
                }
                """,
            ),
            "activity_hint": "Use string concatenation with + to combine text and numbers.",
            "activity_validation": build_code_activity_validation(
                "csharp",
                expected_output=None,
                success_explanation=(
                    "This answer is correct because it compiles and uses a counting loop to repeat the output for five practice days."
                ),
                failure_hint=(
                    "Create a for loop that starts at 1, ends at 5, and prints each practice day."
                ),
                starter_code="""
                using System;

                class Program
                {
                    static void Main()
                    {
                        // Write your loop here
                    }
                }
                """,
                required_patterns=[
                    required_pattern(r"\bfor\s*\(", "a for loop"),
                    required_pattern(r"int\s+i\s*=\s*1", "a loop that starts at 1"),
                    required_pattern(r"i\s*<=\s*5", "a loop condition that reaches 5"),
                    required_pattern(r"Console\.WriteLine\s*\(", "a Console.WriteLine statement in the loop"),
                ],
                min_output_lines=6,
                learning_suggestion="If the compiler succeeds, compare the loop bounds with the number of lines you expect to print.",
            ),
        },
        {
            "title": "Methods and Reusable Logic",
            "slug": "csharp-methods-and-reusable-logic",
            "summary": "Organize code into methods that can be reused.",
            "lecture_content": build_lesson_content(
                [
                    "Methods group related instructions into named units, making a program easier to read and maintain.",
                    "Once you define a method, you can call it whenever the same task is needed again.",
                ],
                """
                using System;

                class Program
                {
                    static void Greet(string name)
                    {
                        Console.WriteLine("Hello, " + name);
                    }

                    static void Main()
                    {
                        Greet("Ivy");
                        Greet("Noah");
                    }
                }
                """,
                [
                    "A method has a return type, a name, and optional parameters.",
                    "Parameters accept values from the caller.",
                    "Methods reduce repetition and improve structure.",
                ],
            ),
            "activity_title": "Activity 5: Study Goal Method",
            "activity_instructions": build_activity_content(
                "Create a method that prints a learning goal.",
                [
                    "Define a method named ShowGoal that receives a string topic.",
                    "Inside the method, print I am practicing plus the topic.",
                    "Call the method two times with different values.",
                ],
                """
                using System;

                class Program
                {
                    static void ShowGoal(string topic)
                    {
                        // Write your Console.WriteLine statement here
                    }

                    static void Main()
                    {
                    }
                }
                """,
            ),
            "activity_hint": "Call a method by writing its name followed by parentheses.",
            "activity_validation": build_code_activity_validation(
                "csharp",
                expected_output=None,
                success_explanation=(
                    "Your answer is correct because it compiles, defines a reusable method with a parameter, and calls it multiple times."
                ),
                failure_hint=(
                    "Define ShowGoal(string topic), print a message inside it, and call ShowGoal() twice."
                ),
                starter_code="""
                using System;

                class Program
                {
                    static void ShowGoal(string topic)
                    {
                        // Write your Console.WriteLine statement here
                    }

                    static void Main()
                    {
                    }
                }
                """,
                required_patterns=[
                    required_pattern(r"static\s+void\s+ShowGoal\s*\(\s*string\s+topic\s*\)", "the ShowGoal(string topic) method"),
                    required_pattern(r"Console\.WriteLine\s*\(", "a Console.WriteLine statement inside the method"),
                    required_pattern(r"ShowGoal\s*\(", "two calls to ShowGoal()", count=3),
                ],
                min_output_lines=2,
                learning_suggestion="Once it compiles, try calling the method with a third topic to reinforce how parameters change output.",
            ),
        },
        {
            "title": "Collections, Simple Problem Solving, and Final Quiz",
            "slug": "csharp-collections-problem-solving-and-final-quiz",
            "summary": "Use arrays or lists to handle multiple values, solve a beginner problem, and finish with the final quiz.",
            "lecture_content": build_lesson_content(
                [
                    "Collections such as arrays and lists allow you to store multiple related values together.",
                    "When you combine collections with loops and methods, you can solve practical beginner problems like totals, counts, and summaries.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        int[] scores = { 88, 76, 94, 81 };
                        int total = 0;

                        foreach (int score in scores)
                        {
                            total += score;
                        }

                        Console.WriteLine("Total: " + total);
                    }
                }
                """,
                [
                    "Arrays store multiple values of the same type.",
                    "foreach reads each value in a collection.",
                    "Problem-solving becomes easier when you break tasks into simple steps.",
                ],
            ),
            "activity_title": "Activity 6: Score Total Calculator",
            "activity_instructions": build_activity_content(
                "Create a C# program that totals several scores.",
                [
                    "Declare an array with at least four scores.",
                    "Use a loop or foreach to compute the total.",
                    "Display the total and the number of scores.",
                ],
                """
                using System;

                class Program
                {
                    static void Main()
                    {
                        int[] scores = { 75, 80, 90, 95 };
                        int total = 0;
                    }
                }
                """,
            ),
            "activity_hint": "Array.Length tells you how many values are inside the array.",
            "activity_validation": build_code_activity_validation(
                "csharp",
                expected_output=None,
                success_explanation=(
                    "This solution is correct because it compiles, stores multiple scores in a collection, iterates through them, and computes a total."
                ),
                failure_hint=(
                    "Create an int[] scores array, loop through it, add each value to total, and print the result."
                ),
                starter_code="""
                using System;

                class Program
                {
                    static void Main()
                    {
                        int[] scores = { 75, 80, 90, 95 };
                        int total = 0;
                    }
                }
                """,
                required_patterns=[
                    required_pattern(r"int\[\]\s+scores", "an integer array named scores"),
                    required_pattern(r"\bforeach\s*\(", "a foreach loop"),
                    required_pattern(r"total\s*\+=", "logic that adds each score to total"),
                    required_pattern(r"Console\.WriteLine\s*\(", "a Console.WriteLine statement for the summary"),
                ],
                min_output_lines=1,
                learning_suggestion="After it runs, compare the total you printed with a hand calculation to check your logic.",
            ),
            "quiz": {
                "title": "C# Final Quiz",
                "instructions": "Answer the final multiple-choice quiz to complete the C# Programming Foundations course.",
                "passing_score": 70,
                "questions": [
                    {
                        "prompt": "Which method displays a line of text in a C# console application?",
                        "choices": ["Console.WriteLine()", "Console.Show()", "print()", "Display()"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "Which data type stores whole numbers in C#?",
                        "choices": ["string", "bool", "int", "double"],
                        "correct_index": 2,
                    },
                    {
                        "prompt": "Which statement is used to check another condition after if in C#?",
                        "choices": ["else if", "repeat", "switch", "case"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "Which loop is ideal for counting from a starting value to an ending value?",
                        "choices": ["for", "break", "if", "class"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "What is the purpose of a method?",
                        "choices": ["To draw graphics only", "To repeat a task in reusable code", "To store only numbers", "To rename variables"],
                        "correct_index": 1,
                    },
                    {
                        "prompt": "Which C# structure lets you store several integers together as one collection?",
                        "choices": ["array", "comment", "namespace", "operator"],
                        "correct_index": 0,
                    },
                ],
            },
        },
    ],
}
