from courses.models import Course

from .builders import (
    build_activity_content,
    build_activity_validation,
    build_lesson_content,
    required_pattern,
)


PYTHON_FOUNDATIONS = {
    "title": "Python Programming Foundations",
    "slug": "python-programming-foundations",
    "description": (
        "Learn Python through progressive beginner-friendly lessons that cover syntax, "
        "variables, decisions, loops, functions, and basic problem-solving."
    ),
    "overview": (
        "After completing this course, the learner will be able to write simple Python programs, "
        "solve small programming tasks, and understand the core building blocks of structured coding."
    ),
    "difficulty": Course.BEGINNER,
    "estimated_hours": 10,
    "lessons": [
        {
            "title": "Getting Started with Python",
            "slug": "getting-started-with-python",
            "summary": "Learn what Python is, how a basic script is structured, and how to display output.",
            "lecture_content": build_lesson_content(
                [
                    "Python is a readable programming language that is widely used for web development, automation, data analysis, and problem-solving.",
                    "A beginner can start quickly because Python code is close to plain English and does not require many symbols to produce visible results.",
                ],
                """
                print("Hello, Python learner!")
                print("Welcome to programming foundations.")
                """,
                [
                    "A Python script runs from top to bottom.",
                    "The print() function displays text or values on the screen.",
                    "Strings are written inside quotation marks.",
                ],
            ),
            "activity_title": "Activity 1: Friendly Program Output",
            "activity_instructions": build_activity_content(
                "Write a short program that introduces the learner and prints a motivational message.",
                [
                    "Print your name on the first line.",
                    "Print the language you are learning on the second line.",
                    "Print a short message such as I can learn programming on the third line.",
                ],
                """
                # Write your three print statements below
                """,
            ),
            "activity_hint": "Use one print() statement for each line of output.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\bprint\s*\(", "three print() statements", count=3),
                    required_pattern(r"(python|programming|learn)", "a learning-related message"),
                ],
                success_explanation=(
                    "Your answer is correct because it uses print() statements to produce multiple lines of output, "
                    "which is the core goal of this beginner activity."
                ),
                failure_hint=(
                    "Use three separate print() statements and include at least one message about learning Python or programming."
                ),
            ),
        },
        {
            "title": "Variables and Data Types",
            "slug": "variables-and-data-types",
            "summary": "Store values in variables and work with strings, integers, and floating-point numbers.",
            "lecture_content": build_lesson_content(
                [
                    "Variables are named containers that hold information your program can use later.",
                    "Python automatically understands common data types such as text, whole numbers, and decimal numbers based on the value you assign.",
                ],
                """
                student_name = "Ana"
                age = 19
                grade_average = 93.5

                print(student_name)
                print(age)
                print(grade_average)
                """,
                [
                    "Use = to assign a value to a variable.",
                    "Strings store text, integers store whole numbers, and floats store decimal values.",
                    "Meaningful variable names make code easier to understand.",
                ],
            ),
            "activity_title": "Activity 2: Personal Data Tracker",
            "activity_instructions": build_activity_content(
                "Create variables that describe a learner and display them clearly.",
                [
                    "Create a variable for a learner name.",
                    "Create a variable for age.",
                    "Create a variable for favorite programming topic.",
                    "Print all values with labels.",
                ],
                """
                learner_name = ""
                learner_age = 0
                favorite_topic = ""
                """,
            ),
            "activity_hint": "You can join text and values with commas inside print().",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\blearner_name\b", "the learner_name variable"),
                    required_pattern(r"\blearner_age\b", "the learner_age variable"),
                    required_pattern(r"\bfavorite_topic\b", "the favorite_topic variable"),
                    required_pattern(r"\bprint\s*\(", "at least one print() statement"),
                ],
                success_explanation=(
                    "This solution is correct because it defines the required variables and displays data using print(), "
                    "showing an understanding of variables and basic output."
                ),
                failure_hint=(
                    "Declare all three named variables and print the stored values so the profile information is visible."
                ),
            ),
        },
        {
            "title": "Conditional Statements",
            "slug": "conditional-statements",
            "summary": "Use if, elif, and else to make decisions based on conditions.",
            "lecture_content": build_lesson_content(
                [
                    "Programs often need to choose between actions. Conditional statements allow the code to react to different situations.",
                    "Python checks a condition that evaluates to True or False and runs the matching block of code.",
                ],
                """
                score = 85

                if score >= 90:
                    print("Excellent")
                elif score >= 75:
                    print("Passed")
                else:
                    print("Needs improvement")
                """,
                [
                    "if starts the first condition.",
                    "elif checks another condition when the first one is false.",
                    "else runs when no earlier condition is true.",
                ],
            ),
            "activity_title": "Activity 3: Pass or Retry Checker",
            "activity_instructions": build_activity_content(
                "Write a program that tells a learner whether they passed a short quiz.",
                [
                    "Create a score variable.",
                    "If the score is 75 or higher, print Passed.",
                    "Otherwise, print Review and try again.",
                ],
                """
                score = 0
                """,
            ),
            "activity_hint": "Use a comparison operator like >= inside an if statement.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\bif\b", "an if statement"),
                    required_pattern(r"score\s*>=\s*75", "a condition that checks score >= 75"),
                    required_pattern(r"passed", "an output for the passed result"),
                    required_pattern(r"(review|try again)", "an output for the retry result"),
                ],
                success_explanation=(
                    "Your answer is correct because it checks a score condition and gives different results for passing and not passing."
                ),
                failure_hint=(
                    "Use an if statement that checks whether score is at least 75, then provide both pass and retry outputs."
                ),
            ),
        },
        {
            "title": "Loops and Repetition",
            "slug": "loops-and-repetition",
            "summary": "Repeat actions efficiently using for loops and while loops.",
            "lecture_content": build_lesson_content(
                [
                    "Loops help you repeat instructions without rewriting the same code many times.",
                    "A for loop is useful when you know how many times to repeat something, while a while loop continues until a condition becomes false.",
                ],
                """
                for number in range(1, 6):
                    print("Round", number)

                countdown = 3
                while countdown > 0:
                    print(countdown)
                    countdown -= 1
                """,
                [
                    "range() generates a sequence of numbers for a for loop.",
                    "A while loop needs a condition that eventually becomes false.",
                    "Loops reduce repetition and make code more efficient.",
                ],
            ),
            "activity_title": "Activity 4: Practice Counter",
            "activity_instructions": build_activity_content(
                "Use a loop to simulate repeated practice sessions.",
                [
                    "Use a for loop to print Practice session 1 to Practice session 5.",
                    "After the loop, print Great job staying consistent.",
                ],
                """
                # Write your loop below
                """,
            ),
            "activity_hint": "range(1, 6) gives you the numbers 1 through 5.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\bfor\b", "a for loop"),
                    required_pattern(r"range\s*\(\s*1\s*,\s*6\s*\)", "range(1, 6)"),
                    required_pattern(r"\bprint\s*\(", "a print() statement inside the loop"),
                ],
                success_explanation=(
                    "This is correct because it uses a for loop with range(1, 6) to repeat an action five times."
                ),
                failure_hint=(
                    "Create a for loop that uses range(1, 6) and prints each practice session number."
                ),
            ),
        },
        {
            "title": "Functions and Reusable Code",
            "slug": "functions-and-reusable-code",
            "summary": "Group instructions into functions so code becomes reusable and organized.",
            "lecture_content": build_lesson_content(
                [
                    "Functions package a task into a named block of code that you can call whenever needed.",
                    "They help you avoid repetition and make programs easier to read, test, and improve.",
                ],
                """
                def greet(name):
                    print("Hello,", name)

                greet("Mika")
                greet("Sam")
                """,
                [
                    "def creates a function.",
                    "Parameters let a function receive input values.",
                    "A function runs only when it is called.",
                ],
            ),
            "activity_title": "Activity 5: Build a Greeting Function",
            "activity_instructions": build_activity_content(
                "Create a function that displays a custom learning message.",
                [
                    "Define a function named show_goal that accepts one parameter called topic.",
                    "Inside the function, print I am learning followed by the topic.",
                    "Call the function at least two times with different topics.",
                ],
                """
                def show_goal(topic):
                    # Write your print statement here
                    pass
                """,
            ),
            "activity_hint": "A parameter acts like a variable inside the function.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"def\s+show_goal\s*\(\s*topic\s*\)", "the show_goal(topic) function definition"),
                    required_pattern(r"\bprint\s*\(", "a print() statement in the function"),
                    required_pattern(r"show_goal\s*\(", "two calls to show_goal()", count=3),
                ],
                success_explanation=(
                    "Your solution is correct because it defines a reusable function with a parameter and calls it more than once."
                ),
                failure_hint=(
                    "Define show_goal(topic), print a message inside it, and call show_goal() two separate times."
                ),
            ),
        },
        {
            "title": "Lists, Problem Solving, and Final Quiz",
            "slug": "lists-problem-solving-and-final-quiz",
            "summary": "Store multiple values in a list, solve a small problem, and complete the final course quiz.",
            "lecture_content": build_lesson_content(
                [
                    "Lists let you store several related values in one variable. They are useful for tracking scores, names, or repeated items.",
                    "Combining lists with loops and functions helps you solve practical beginner-level problems such as totals, counts, and simple summaries.",
                ],
                """
                scores = [88, 91, 79, 95]
                total = 0

                for score in scores:
                    total += score

                average = total / len(scores)
                print("Average:", average)
                """,
                [
                    "Lists are created with square brackets.",
                    "You can loop through list items one by one.",
                    "Breaking a problem into steps makes coding easier.",
                ],
            ),
            "activity_title": "Activity 6: Score Summary Program",
            "activity_instructions": build_activity_content(
                "Create a short program that works with a list of scores.",
                [
                    "Create a list with at least four quiz scores.",
                    "Use a loop to compute the total score.",
                    "Display the number of scores and the total.",
                    "If you want an extra challenge, compute the average too.",
                ],
                """
                scores = [75, 80, 90, 95]
                total = 0
                """,
            ),
            "activity_hint": "Start with total = 0 and add each score inside the loop.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\bscores\s*=\s*\[", "a scores list"),
                    required_pattern(r"\bfor\s+\w+\s+in\s+scores\b", "a loop through the scores list"),
                    required_pattern(r"total\s*\+=", "logic that adds each score to total"),
                    required_pattern(r"\bprint\s*\(", "a print() statement for the summary"),
                ],
                success_explanation=(
                    "This answer is correct because it stores multiple scores in a list, loops through them, and calculates a running total."
                ),
                failure_hint=(
                    "Use a scores list, loop through each value, add to total, and print the final summary."
                ),
            ),
            "quiz": {
                "title": "Python Final Quiz",
                "instructions": "Answer the final multiple-choice quiz to complete the Python Programming Foundations course.",
                "passing_score": 70,
                "questions": [
                    {
                        "prompt": "Which function displays text on the screen in Python?",
                        "choices": ["echo()", "print()", "show()", "write()"],
                        "correct_index": 1,
                    },
                    {
                        "prompt": "Which symbol is used to assign a value to a variable?",
                        "choices": ["==", "=", ":", "->"],
                        "correct_index": 1,
                    },
                    {
                        "prompt": "Which statement runs when the previous if condition is false and another condition must be checked?",
                        "choices": ["loop", "elif", "try", "pass"],
                        "correct_index": 1,
                    },
                    {
                        "prompt": "What does range(1, 6) produce in a for loop?",
                        "choices": ["1 to 5", "1 to 6", "0 to 6", "Only 6"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "What keyword is used to define a function in Python?",
                        "choices": ["function", "define", "def", "func"],
                        "correct_index": 2,
                    },
                    {
                        "prompt": "Which data structure is written with square brackets?",
                        "choices": ["Tuple", "List", "Dictionary", "Function"],
                        "correct_index": 1,
                    },
                ],
            },
        },
    ],
}
