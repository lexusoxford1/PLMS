from courses.models import Course

from .builders import (
    build_activity_content,
    build_code_activity_validation,
    build_lesson_content,
    required_pattern,
)


PYTHON_FOUNDATIONS = {
    "title": "Python Programming Foundations",
    "slug": "python-programming-foundations",
    "description": (
        "Build a strong start in Python with progressive lessons on syntax, variables, conditions, loops, functions, collections, and problem-solving."
    ),
    "overview": (
        "After completing this course, the learner will be able to write simple Python programs, "
        "use core control structures, and organize beginner-level solutions using functions and collections."
    ),
    "difficulty": Course.BEGINNER,
    "estimated_hours": 10,
    "lessons": [
        {
            "title": "Getting Started with Python",
            "slug": "getting-started-with-python",
            "summary": "Understand the structure of a Python script and display output.",
            "lecture_content": build_lesson_content(
                [
                    "Python is a beginner-friendly programming language used for automation, web development, data analysis, and problem-solving.",
                    "A simple script is a great place to begin because it helps you focus on core programming logic without interface complexity.",
                ],
                """
                print("Hello, Python learner!")
                print("Welcome to programming foundations.")
                """,
                [
                    "A Python script runs from top to bottom.",
                    "print() displays output and moves to the next line.",
                    "Strings are written inside quotation marks.",
                ],
            ),
            "activity_title": "Activity 1: Script Introduction",
            "activity_instructions": build_activity_content(
                "Write a short Python program that introduces the learner.",
                [
                    "Print your name on one line.",
                    "Print I am learning Python on the next line.",
                    "Print one more motivational message.",
                ],
                """
                # Write your print() statements below
                """,
            ),
            "activity_hint": "Each print() call displays one full line.",
            "activity_validation": build_code_activity_validation(
                "python",
                expected_output=None,
                success_explanation=(
                    "Your answer is correct because it runs successfully and uses print() multiple times to produce clear console output."
                ),
                failure_hint=(
                    "Use at least three print() statements and include a line about Python or learning."
                ),
                starter_code="""
                # Write your print() statements below
                """,
                required_patterns=[
                    required_pattern(r"\bprint\s*\(", "three print() statements", count=3),
                    required_pattern(r"(Python|learning)", "a message about Python or learning"),
                ],
                min_output_lines=3,
                learning_suggestion="Try changing one printed line and run the code again to see how the output changes.",
            ),
        },
        {
            "title": "Variables and Data Types",
            "slug": "python-variables-and-data-types",
            "summary": "Declare variables and use strings, integers, floats, and booleans.",
            "lecture_content": build_lesson_content(
                [
                    "Variables store data that your program can read and update.",
                    "Python infers data types from assigned values such as str, int, float, and bool.",
                ],
                """
                student_name = "Carlo"
                age = 18
                average = 92.5
                is_enrolled = True

                print(student_name)
                print(age)
                print(average)
                print(is_enrolled)
                """,
                [
                    "str stores text, int stores whole numbers, float stores decimals, and bool stores True or False.",
                    "A variable assignment usually includes a name, =, and a value.",
                    "Clear variable names make code easier to understand.",
                ],
            ),
            "activity_title": "Activity 2: Student Information Program",
            "activity_instructions": build_activity_content(
                "Create variables that describe a learner and display them.",
                [
                    "Declare a name variable.",
                    "Declare an age variable.",
                    "Declare a bool variable for whether the learner is ready.",
                    "Print all values using print().",
                ],
                """
                name = ""
                age = 0
                is_ready = False
                """,
            ),
            "activity_hint": "Use separate print() statements so each value is easy to read.",
            "activity_validation": build_code_activity_validation(
                "python",
                expected_output=None,
                success_explanation=(
                    "This is correct because it declares the expected Python variables, runs successfully, and outputs them using print()."
                ),
                failure_hint=(
                    "Declare name, age, and is_ready, then print them with print()."
                ),
                starter_code="""
                name = ""
                age = 0
                is_ready = False
                """,
                required_patterns=[
                    required_pattern(r"\bname\b", "a name variable"),
                    required_pattern(r"\bage\b", "an age variable"),
                    required_pattern(r"\bis_ready\b", "a bool is_ready variable"),
                    required_pattern(r"\bprint\s*\(", "a print() statement"),
                ],
                min_output_lines=3,
                learning_suggestion="After it runs, try changing one variable value and rerun the code to see how the output updates.",
            ),
        },
        {
            "title": "Conditional Statements",
            "slug": "python-conditional-statements",
            "summary": "Make decisions using if, elif, and else.",
            "lecture_content": build_lesson_content(
                [
                    "Programs make decisions by checking conditions that evaluate to True or False.",
                    "In Python, conditional statements let you choose which block of code should run in a given situation.",
                ],
                """
                score = 84

                if score >= 90:
                    print("Excellent")
                elif score >= 75:
                    print("Passed")
                else:
                    print("Needs improvement")
                """,
                [
                    "if checks the first condition.",
                    "elif checks another condition when needed.",
                    "else handles the remaining case.",
                ],
            ),
            "activity_title": "Activity 3: Result Evaluator",
            "activity_instructions": build_activity_content(
                "Write a program that checks whether a learner passed.",
                [
                    "Declare a score variable.",
                    "If the score is 75 or higher, print Passed.",
                    "Otherwise, print Study and try again.",
                ],
                """
                score = 0
                """,
            ),
            "activity_hint": "Conditions in Python end with a colon.",
            "activity_validation": build_code_activity_validation(
                "python",
                expected_output=None,
                success_explanation=(
                    "Your solution is correct because it runs and uses conditional logic to separate passing and non-passing outcomes."
                ),
                failure_hint=(
                    "Use an if statement with score >= 75 and include both a pass message and a retry message."
                ),
                starter_code="""
                score = 0
                """,
                required_patterns=[
                    required_pattern(r"\bif\b", "an if statement"),
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
                learning_suggestion="Trace which branch should run for the score value you chose before running the code again.",
            ),
        },
        {
            "title": "Loops and Repetition",
            "slug": "python-loops-and-repetition",
            "summary": "Repeat tasks with for and while loops.",
            "lecture_content": build_lesson_content(
                [
                    "Loops allow a program to repeat instructions efficiently instead of copying the same code many times.",
                    "A for loop is useful for counting, while a while loop is helpful when repetition depends on a changing condition.",
                ],
                """
                for i in range(1, 6):
                    print("Practice round", i)

                countdown = 3
                while countdown > 0:
                    print(countdown)
                    countdown -= 1
                """,
                [
                    "for loops are useful for counters and sequences.",
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
                # Write your loop here
                """,
            ),
            "activity_hint": "Use an f-string or commas in print() to combine text and numbers.",
            "activity_validation": build_code_activity_validation(
                "python",
                expected_output=None,
                success_explanation=(
                    "This answer is correct because it runs and uses a counting loop to repeat the output for five practice days."
                ),
                failure_hint=(
                    "Create a for loop that starts at 1, ends at 5, and prints each practice day."
                ),
                starter_code="""
                # Write your loop here
                """,
                required_patterns=[
                    required_pattern(r"\bfor\b", "a for loop"),
                    required_pattern(r"range\s*\(\s*1\s*,\s*6\s*\)", "a loop that starts at 1 and reaches 5"),
                    required_pattern(r"\bprint\s*\(", "a print() statement in the loop"),
                ],
                min_output_lines=6,
                learning_suggestion="If the runner succeeds, compare the loop bounds with the number of lines you expect to print.",
            ),
        },
        {
            "title": "Functions and Reusable Logic",
            "slug": "python-functions-and-reusable-logic",
            "summary": "Organize code into functions that can be reused.",
            "lecture_content": build_lesson_content(
                [
                    "Functions group related instructions into named units, making a program easier to read and maintain.",
                    "Once you define a function, you can call it whenever the same task is needed again.",
                ],
                """
                def show_goal(topic):
                    print("I am practicing", topic)

                show_goal("loops")
                show_goal("functions")
                """,
                [
                    "A function has a name and optional parameters.",
                    "Parameters accept values from the caller.",
                    "Functions reduce repetition and improve structure.",
                ],
            ),
            "activity_title": "Activity 5: Study Goal Function",
            "activity_instructions": build_activity_content(
                "Create a function that prints a learning goal.",
                [
                    "Define a function named show_goal that receives a topic parameter.",
                    "Inside the function, print I am practicing plus the topic.",
                    "Call the function two times with different values.",
                ],
                """
                def show_goal(topic):
                    # Write your print() statement here
                    pass
                """,
            ),
            "activity_hint": "Call a function by writing its name followed by parentheses.",
            "activity_validation": build_code_activity_validation(
                "python",
                expected_output=None,
                success_explanation=(
                    "Your answer is correct because it runs, defines a reusable function with a parameter, and calls it multiple times."
                ),
                failure_hint=(
                    "Define show_goal(topic), print a message inside it, and call show_goal() twice."
                ),
                starter_code="""
                def show_goal(topic):
                    # Write your print() statement here
                    pass
                """,
                required_patterns=[
                    required_pattern(r"def\s+show_goal\s*\(\s*topic\s*\)", "the show_goal(topic) function"),
                    required_pattern(r"\bprint\s*\(", "a print() statement inside the function"),
                    required_pattern(r"show_goal\s*\(", "two calls to show_goal()", count=3),
                ],
                min_output_lines=2,
                learning_suggestion="Once it runs, try calling the function with a third topic to reinforce how parameters change output.",
            ),
        },
        {
            "title": "Collections, Simple Problem Solving, and Final Quiz",
            "slug": "python-collections-problem-solving-and-final-quiz",
            "summary": "Use lists to handle multiple values, solve a beginner problem, and finish with the final quiz.",
            "lecture_content": build_lesson_content(
                [
                    "Collections such as lists allow you to store multiple related values together.",
                    "When you combine collections with loops and functions, you can solve practical beginner problems like totals, counts, and summaries.",
                ],
                """
                scores = [88, 76, 94, 81]
                total = 0

                for score in scores:
                    total += score

                print("Total:", total)
                """,
                [
                    "Lists store multiple values in one variable.",
                    "for reads each value in a collection.",
                    "Problem-solving becomes easier when you break tasks into simple steps.",
                ],
            ),
            "activity_title": "Activity 6: Score Total Calculator",
            "activity_instructions": build_activity_content(
                "Create a Python program that totals several scores.",
                [
                    "Declare a list with at least four scores.",
                    "Use a loop to compute the total.",
                    "Display the total and the number of scores.",
                ],
                """
                scores = [75, 80, 90, 95]
                total = 0
                """,
            ),
            "activity_hint": "len(scores) tells you how many values are inside the list.",
            "activity_validation": build_code_activity_validation(
                "python",
                expected_output=None,
                success_explanation=(
                    "This solution is correct because it runs, stores multiple scores in a collection, iterates through them, and computes a total."
                ),
                failure_hint=(
                    "Create a scores list, loop through it, add each value to total, and print the result."
                ),
                starter_code="""
                scores = [75, 80, 90, 95]
                total = 0
                """,
                required_patterns=[
                    required_pattern(r"\bscores\s*=\s*\[", "a scores list"),
                    required_pattern(r"\bfor\s+\w+\s+in\s+scores\b", "a loop through the scores list"),
                    required_pattern(r"total\s*\+=", "logic that adds each score to total"),
                    required_pattern(r"\bprint\s*\(", "a print() statement for the summary"),
                ],
                min_output_lines=1,
                learning_suggestion="After it runs, compare the total you printed with a hand calculation to check your logic.",
            ),
            "quiz": {
                "title": "Python Final Quiz",
                "instructions": "Answer the final multiple-choice quiz to complete the Python Programming Foundations course.",
                "passing_score": 70,
                "questions": [
                    {
                        "prompt": "Which function displays a line of text in a Python script?",
                        "choices": ["print()", "show()", "Console.WriteLine()", "Display()"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "Which data type stores whole numbers in Python?",
                        "choices": ["str", "bool", "int", "float"],
                        "correct_index": 2,
                    },
                    {
                        "prompt": "Which statement is used to check another condition after if in Python?",
                        "choices": ["elif", "repeat", "switch", "case"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "Which loop is ideal for counting from a starting value to an ending value in Python?",
                        "choices": ["for", "break", "if", "class"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "What is the purpose of a function?",
                        "choices": ["To draw graphics only", "To repeat a task in reusable code", "To store only numbers", "To rename variables"],
                        "correct_index": 1,
                    },
                    {
                        "prompt": "Which Python structure lets you store several integers together as one collection?",
                        "choices": ["list", "comment", "module", "operator"],
                        "correct_index": 0,
                    },
                ],
            },
        },
    ],
}
