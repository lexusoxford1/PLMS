from courses.models import Course

from .builders import (
    build_activity_content,
    build_code_activity_validation,
    build_lesson_content,
    required_pattern,
)


PHP_FOUNDATIONS = {
    "title": "PHP Programming Foundations",
    "slug": "php-programming-foundations",
    "description": (
        "Build a strong start in PHP with progressive lessons on syntax, variables, conditions, loops, functions, arrays, and problem-solving."
    ),
    "overview": (
        "After completing this course, the learner will be able to write simple PHP scripts, "
        "use core control structures, and organize beginner-level solutions using functions and arrays."
    ),
    "difficulty": Course.BEGINNER,
    "estimated_hours": 10,
    "lessons": [
        {
            "title": "Getting Started with PHP",
            "slug": "getting-started-with-php",
            "summary": "Understand the structure of a PHP script and display output in the course runner.",
            "lecture_content": build_lesson_content(
                [
                    "PHP is a popular scripting language used for web development, automation, and server-side logic.",
                    "A simple CLI-style script is a great place to begin because it helps you focus on core programming logic without interface complexity.",
                ],
                """
                <?php
                echo "Hello, PHP learner!" . PHP_EOL;
                echo "Welcome to programming foundations." . PHP_EOL;
                """,
                [
                    "PHP code usually starts with <?php.",
                    "echo outputs text or values.",
                    "Statements usually end with a semicolon.",
                ],
            ),
            "activity_title": "Activity 1: Script Introduction",
            "activity_instructions": build_activity_content(
                "Write a short PHP program that introduces the learner.",
                [
                    "Print your name on one line.",
                    "Print I am learning PHP on the next line.",
                    "Print one more motivational message.",
                ],
                """
                <?php
                // Write your echo statements here
                """,
            ),
            "activity_hint": "Use PHP_EOL or \\n if you want each echo to appear on a new line.",
            "activity_validation": build_code_activity_validation(
                "php",
                expected_output=None,
                expected_output_contains=["I am learning PHP"],
                success_explanation=(
                    "Your answer is correct because it runs successfully and uses echo multiple times to produce clear console output."
                ),
                failure_hint=(
                    "Use at least three echo statements and include a line about PHP or learning."
                ),
                starter_code="""
                <?php
                // Write your echo statements here
                """,
                required_patterns=[
                    required_pattern(r"\becho\b", "three echo statements", count=3),
                    required_pattern(r"(PHP|learning)", "a message about PHP or learning"),
                ],
                ignore_case=True,
                min_output_lines=3,
                learning_suggestion="Try changing one printed line and run the code again to see how the output changes.",
                accept_alternative_solutions=True,
            ),
        },
        {
            "title": "Variables and Data Types",
            "slug": "php-variables-and-data-types",
            "summary": "Declare variables and use strings, integers, floats, and booleans.",
            "lecture_content": build_lesson_content(
                [
                    "Variables store data that your program can read and update.",
                    "In PHP, variables begin with a dollar sign and can hold values such as strings, integers, floats, and booleans.",
                ],
                """
                <?php
                $studentName = "Lia";
                $age = 20;
                $average = 91.4;
                $isReady = true;

                echo $studentName . PHP_EOL;
                echo $age . PHP_EOL;
                echo $average . PHP_EOL;
                echo ($isReady ? "true" : "false") . PHP_EOL;
                """,
                [
                    "Variable names in PHP begin with $.",
                    "Strings store text, integers store whole numbers, floats store decimals, and booleans store true or false.",
                    "Clear variable names improve readability.",
                ],
            ),
            "activity_title": "Activity 2: Student Information Program",
            "activity_instructions": build_activity_content(
                "Create variables that describe a learner and display them.",
                [
                    "Declare a variable for name.",
                    "Declare a variable for age.",
                    "Declare a bool variable for whether the learner is ready.",
                    "Print all values using echo.",
                ],
                """
                <?php
                $name = "";
                $age = 0;
                $isReady = true;
                """,
            ),
            "activity_hint": "Use the . operator to join text and values, and convert the bool to text if you want a clearer final line.",
            "activity_validation": build_code_activity_validation(
                "php",
                expected_output=None,
                success_explanation=(
                    "This is correct because it declares the expected PHP variables, runs successfully, and outputs them using echo."
                ),
                failure_hint=(
                    "Declare $name, $age, and $isReady, then print them with echo."
                ),
                starter_code="""
                <?php
                $name = "";
                $age = 0;
                $isReady = true;
                """,
                required_patterns=[
                    required_pattern(r"\$name\b", "the $name variable"),
                    required_pattern(r"\$age\b", "the $age variable"),
                    required_pattern(r"\$isReady\b", "the $isReady variable"),
                    required_pattern(r"\becho\b", "an echo statement"),
                ],
                ignore_case=True,
                min_output_lines=2,
                learning_suggestion="After it runs, try changing one variable value and rerun the code to see how the output updates.",
                accept_alternative_solutions=True,
            ),
        },
        {
            "title": "Conditional Statements",
            "slug": "php-conditional-statements",
            "summary": "Make decisions using if, elseif, and else.",
            "lecture_content": build_lesson_content(
                [
                    "Programs make decisions by checking conditions that evaluate to true or false.",
                    "In PHP, conditional statements let you choose which block of code should run in a given situation.",
                ],
                """
                <?php
                $score = 82;

                if ($score >= 90) {
                    echo "Excellent" . PHP_EOL;
                } elseif ($score >= 75) {
                    echo "Passed" . PHP_EOL;
                } else {
                    echo "Needs improvement" . PHP_EOL;
                }
                """,
                [
                    "if checks the first condition.",
                    "elseif adds another condition when needed.",
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
                <?php
                $score = 0;
                """,
            ),
            "activity_hint": "Remember that PHP conditions go inside parentheses.",
            "activity_validation": build_code_activity_validation(
                "php",
                expected_output=None,
                expected_output_patterns=[r"\b(Passed|Study and try again)\b"],
                success_explanation=(
                    "Your solution is correct because it runs and uses conditional logic to separate passing and non-passing outcomes."
                ),
                failure_hint=(
                    "Use an if statement with $score >= 75 and include both a pass message and a retry message."
                ),
                starter_code="""
                <?php
                $score = 0;
                """,
                required_patterns=[
                    required_pattern(r"\bif\s*\(", "an if statement"),
                    required_pattern(r"\$score\s*>=\s*75", "a condition that checks $score >= 75"),
                    required_pattern(r"Passed", "a passed output"),
                    required_pattern(r"(Study|try again)", "a retry message"),
                ],
                ignore_case=True,
                min_output_lines=1,
                concept_review={
                    "title": "Concept Review",
                    "badge": "Unlocked after success",
                    "summary": "Conditional logic helps a program choose between different outcomes.",
                    "body": (
                        "This activity uses an if/else decision. The condition $score >= 75 checks whether the "
                        "learner passed. If that condition is true, the program prints Passed. Otherwise, the else "
                        "block runs and prints Study and try again."
                    ),
                },
                learning_suggestion="Trace which branch should run for the score value you chose before running the code again.",
                accept_alternative_solutions=True,
            ),
        },
        {
            "title": "Loops and Repetition",
            "slug": "php-loops-and-repetition",
            "summary": "Repeat tasks with for and while loops.",
            "lecture_content": build_lesson_content(
                [
                    "Loops allow a program to repeat instructions efficiently instead of copying the same code many times.",
                    "A for loop is useful for counting, while a while loop is helpful when repetition depends on a changing condition.",
                ],
                """
                <?php
                for ($i = 1; $i <= 5; $i++) {
                    echo "Practice round " . $i . PHP_EOL;
                }

                $countdown = 3;
                while ($countdown > 0) {
                    echo $countdown . PHP_EOL;
                    $countdown--;
                }
                """,
                [
                    "for loops combine start, condition, and update in one line.",
                    "while loops continue until the condition becomes false.",
                    "Loops are useful for counters, lists, and repeated output.",
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
                <?php
                // Write your loop here
                """,
            ),
            "activity_hint": "Use . to combine text and numbers inside echo.",
            "activity_validation": build_code_activity_validation(
                "php",
                expected_output=None,
                expected_output_contains=["Practice day", "Keep going"],
                success_explanation=(
                    "This answer is correct because it runs and uses a counting loop to repeat the output for five practice days."
                ),
                failure_hint=(
                    "Create a for loop that starts at 1, ends at 5, and prints each practice day."
                ),
                starter_code="""
                <?php
                // Write your loop here
                """,
                required_patterns=[
                    required_pattern(r"\bfor\s*\(", "a for loop"),
                    required_pattern(r"\$i\s*=\s*1", "a loop that starts at 1"),
                    required_pattern(r"\$i\s*<=\s*5", "a loop condition that goes to 5"),
                    required_pattern(r"\becho\b", "an echo statement in the loop"),
                ],
                ignore_case=True,
                min_output_lines=6,
                learning_suggestion="If the runner succeeds, compare the loop bounds with the number of lines you expect to print.",
                accept_alternative_solutions=True,
            ),
        },
        {
            "title": "Functions and Reusable Logic",
            "slug": "php-functions-and-reusable-logic",
            "summary": "Organize code into functions that can be reused.",
            "lecture_content": build_lesson_content(
                [
                    "Functions group related instructions into named units, making a program easier to read and maintain.",
                    "Once you define a function, you can call it whenever the same task is needed again.",
                ],
                """
                <?php
                function showGoal($topic) {
                    echo "I am practicing " . $topic . PHP_EOL;
                }

                showGoal("loops");
                showGoal("functions");
                """,
                [
                    "function defines a reusable block of code.",
                    "Parameters pass input values into the function.",
                    "Calling a function runs the code inside it.",
                ],
            ),
            "activity_title": "Activity 5: Study Goal Function",
            "activity_instructions": build_activity_content(
                "Create a function that prints a learning goal.",
                [
                    "Define a function named showGoal that receives a topic parameter.",
                    "Inside the function, print I am practicing plus the topic.",
                    "Call the function two times with different values.",
                ],
                """
                <?php
                function showGoal($topic) {
                    // Write your echo statement here
                }
                """,
            ),
            "activity_hint": "A parameter works like a variable inside the function body.",
            "activity_validation": build_code_activity_validation(
                "php",
                expected_output=None,
                expected_output_contains=["I am practicing"],
                success_explanation=(
                    "Your answer is correct because it runs, defines a reusable function with a parameter, and calls it multiple times."
                ),
                failure_hint=(
                    "Define showGoal($topic), print a message inside it, and call showGoal() twice."
                ),
                starter_code="""
                <?php
                function showGoal($topic) {
                    // Write your echo statement here
                }
                """,
                required_patterns=[
                    required_pattern(r"function\s+showGoal\s*\(\s*\$topic\s*\)", "the showGoal($topic) function"),
                    required_pattern(r"\becho\b", "an echo statement inside the function"),
                    required_pattern(r"showGoal\s*\(", "two calls to showGoal()", count=3),
                ],
                ignore_case=True,
                min_output_lines=2,
                learning_suggestion="Once it runs, try calling the function with a third topic to reinforce how parameters change output.",
                accept_alternative_solutions=True,
            ),
        },
        {
            "title": "Arrays, Simple Problem Solving, and Final Quiz",
            "slug": "php-arrays-problem-solving-and-final-quiz",
            "summary": "Use arrays to handle multiple values, solve a beginner problem, and finish with the final quiz.",
            "lecture_content": build_lesson_content(
                [
                    "Arrays allow you to store multiple related values together.",
                    "When you combine arrays with loops and functions, you can solve practical beginner problems like totals, counts, and summaries.",
                ],
                """
                <?php
                $scores = [88, 76, 94, 81];
                $total = 0;

                foreach ($scores as $score) {
                    $total += $score;
                }

                echo "Total: " . $total . PHP_EOL;
                """,
                [
                    "Arrays in PHP can be written with square brackets.",
                    "foreach is useful for reading each array item.",
                    "Breaking a problem into steps helps you code with confidence.",
                ],
            ),
            "activity_title": "Activity 6: Score Total Calculator",
            "activity_instructions": build_activity_content(
                "Create a PHP script that works with an array of scores.",
                [
                    "Create an array with at least four values.",
                    "Use a loop to compute the total.",
                    "Echo the total and the number of items in the array.",
                ],
                """
                <?php
                $scores = [70, 85, 90, 95];
                $total = 0;
                """,
            ),
            "activity_hint": "count($scores) gives you the number of values in the array.",
            "activity_validation": build_code_activity_validation(
                "php",
                expected_output=None,
                expected_output_contains=["Total"],
                success_explanation=(
                    "This solution is correct because it runs, stores multiple scores in an array, iterates through them, and computes a total."
                ),
                failure_hint=(
                    "Use a $scores array, iterate with foreach, add each score to $total, and echo the result."
                ),
                starter_code="""
                <?php
                $scores = [70, 85, 90, 95];
                $total = 0;
                """,
                required_patterns=[
                    required_pattern(r"\$scores\s*=\s*\[", "a $scores array"),
                    required_pattern(r"\bforeach\s*\(", "a foreach loop"),
                    required_pattern(r"total\s*\+=", "logic that adds each score to $total"),
                    required_pattern(r"\becho\b", "an echo statement for the result"),
                ],
                ignore_case=True,
                min_output_lines=1,
                learning_suggestion="After it runs, compare the total you printed with a hand calculation to check your logic.",
                accept_alternative_solutions=True,
            ),
            "quiz": {
                "title": "PHP Final Quiz",
                "instructions": "Answer the final multiple-choice quiz to complete the PHP Programming Foundations course.",
                "passing_score": 70,
                "questions": [
                    {
                        "prompt": "Which PHP statement is commonly used to display output?",
                        "choices": ["printLine", "echo", "show", "display"],
                        "correct_index": 1,
                    },
                    {
                        "prompt": "How do PHP variable names begin?",
                        "choices": ["With #", "With @", "With $", "With %"],
                        "correct_index": 2,
                    },
                    {
                        "prompt": "Which keyword checks another condition after if in PHP?",
                        "choices": ["elseif", "repeat", "switch", "loop"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "Which loop is useful when you know the start, condition, and update values?",
                        "choices": ["for", "case", "switch", "break"],
                        "correct_index": 0,
                    },
                    {
                        "prompt": "What keyword is used to define a function in PHP?",
                        "choices": ["method", "func", "def", "function"],
                        "correct_index": 3,
                    },
                    {
                        "prompt": "Which PHP structure is commonly used to loop through each item in an array?",
                        "choices": ["foreach", "if", "echo", "class"],
                        "correct_index": 0,
                    },
                ],
            },
        },
    ],
}
