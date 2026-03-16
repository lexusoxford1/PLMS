from courses.models import Course

from .builders import (
    build_activity_content,
    build_activity_validation,
    build_lesson_content,
    required_pattern,
)


PHP_FOUNDATIONS = {
    "title": "PHP Programming Foundations",
    "slug": "php-programming-foundations",
    "description": (
        "Study core PHP syntax and logic through guided lessons on variables, control flow, functions, arrays, and beginner problem-solving."
    ),
    "overview": (
        "After completing this course, the learner will be able to write basic PHP scripts, process simple program logic, "
        "and understand the foundations needed for web-oriented programming."
    ),
    "difficulty": Course.BEGINNER,
    "estimated_hours": 10,
    "lessons": [
        {
            "title": "Getting Started with PHP",
            "slug": "getting-started-with-php",
            "summary": "Learn PHP opening tags, output statements, and the role of server-side scripting.",
            "lecture_content": build_lesson_content(
                [
                    "PHP is a server-side programming language often used to create dynamic web pages and process form data.",
                    "Even when you begin with simple scripts, you are already learning the logic that powers many web applications.",
                ],
                """
                <?php
                echo "Hello, PHP learner!";
                echo "<br>";
                echo "Welcome to programming foundations.";
                ?>
                """,
                [
                    "PHP code starts inside <?php and ends with ?>.",
                    "echo outputs text or values.",
                    "Statements usually end with a semicolon.",
                ],
            ),
            "activity_title": "Activity 1: Basic PHP Output",
            "activity_instructions": build_activity_content(
                "Create a simple PHP script that prints a short introduction.",
                [
                    "Use echo to display your name.",
                    "Display the phrase I am learning PHP.",
                    "Display one more encouraging line.",
                ],
                """
                <?php
                // Write your echo statements here
                ?>
                """,
            ),
            "activity_hint": "Each echo line should end with a semicolon.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\becho\b", "three echo statements", count=3),
                    required_pattern(r"(php|learning)", "a message about PHP or learning"),
                ],
                success_explanation=(
                    "Your answer is correct because it uses echo statements to display multiple lines of output in a PHP script."
                ),
                failure_hint=(
                    "Use at least three echo statements and include a line that mentions PHP or learning."
                ),
            ),
        },
        {
            "title": "Variables and Data Types",
            "slug": "php-variables-and-data-types",
            "summary": "Store values in variables and use strings, integers, and floating-point numbers.",
            "lecture_content": build_lesson_content(
                [
                    "In PHP, a variable starts with a dollar sign. Variables allow your script to keep data that can be reused or updated later.",
                    "PHP supports common data types such as strings for text, integers for whole numbers, and floats for decimal numbers.",
                ],
                """
                <?php
                $studentName = "Lia";
                $age = 20;
                $average = 91.4;

                echo $studentName;
                echo "<br>";
                echo $age;
                echo "<br>";
                echo $average;
                ?>
                """,
                [
                    "Variable names in PHP begin with $.",
                    "Strings, integers, and floats are common basic data types.",
                    "Clear variable names improve readability.",
                ],
            ),
            "activity_title": "Activity 2: Learner Profile Variables",
            "activity_instructions": build_activity_content(
                "Create variables for a simple learner profile and display them.",
                [
                    "Create a variable for name.",
                    "Create a variable for age.",
                    "Create a variable for favorite language feature.",
                    "Echo each value with a label.",
                ],
                """
                <?php
                $name = "";
                $age = 0;
                $favoriteFeature = "";
                ?>
                """,
            ),
            "activity_hint": "You can join strings and variables using the . operator in PHP.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\$name\b", "the $name variable"),
                    required_pattern(r"\$age\b", "the $age variable"),
                    required_pattern(r"\$favoriteFeature\b", "the $favoriteFeature variable"),
                    required_pattern(r"\becho\b", "an echo statement"),
                ],
                success_explanation=(
                    "This is correct because it declares the required PHP variables and displays learner information with echo."
                ),
                failure_hint=(
                    "Create the named variables with $ and echo their values so the learner profile is shown."
                ),
            ),
        },
        {
            "title": "Conditional Statements",
            "slug": "php-conditional-statements",
            "summary": "Decide between actions using if, elseif, and else.",
            "lecture_content": build_lesson_content(
                [
                    "Conditional statements make a program responsive. They let your script react differently based on scores, choices, or input values.",
                    "PHP checks conditions in order and runs the first matching block.",
                ],
                """
                <?php
                $score = 82;

                if ($score >= 90) {
                    echo "Excellent";
                } elseif ($score >= 75) {
                    echo "Passed";
                } else {
                    echo "Needs improvement";
                }
                ?>
                """,
                [
                    "if checks the first condition.",
                    "elseif adds another condition when needed.",
                    "else handles the remaining case.",
                ],
            ),
            "activity_title": "Activity 3: Grade Feedback Checker",
            "activity_instructions": build_activity_content(
                "Write a PHP script that gives feedback for a learner score.",
                [
                    "Create a score variable.",
                    "If the score is 75 or higher, echo Passed.",
                    "Otherwise, echo Study and try again.",
                ],
                """
                <?php
                $score = 0;
                ?>
                """,
            ),
            "activity_hint": "Remember that PHP conditions go inside parentheses.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\bif\s*\(", "an if statement"),
                    required_pattern(r"\$score\s*>=\s*75", "a condition that checks $score >= 75"),
                    required_pattern(r"passed", "a passed output"),
                    required_pattern(r"(study|try again)", "a retry message"),
                ],
                success_explanation=(
                    "Your solution is correct because it uses conditional logic to separate passing and non-passing results."
                ),
                failure_hint=(
                    "Use an if condition with $score >= 75, then provide both a passing message and a retry message."
                ),
            ),
        },
        {
            "title": "Loops and Repetition",
            "slug": "php-loops-and-repetition",
            "summary": "Use loops to repeat actions using for and while.",
            "lecture_content": build_lesson_content(
                [
                    "Loops reduce repetitive code and let you process repeated tasks efficiently.",
                    "A for loop is helpful when you know the number of repetitions, while a while loop continues as long as a condition remains true.",
                ],
                """
                <?php
                for ($i = 1; $i <= 5; $i++) {
                    echo "Practice round " . $i . "<br>";
                }

                $countdown = 3;
                while ($countdown > 0) {
                    echo $countdown . "<br>";
                    $countdown--;
                }
                ?>
                """,
                [
                    "for loops combine start, condition, and update in one line.",
                    "while loops continue until the condition becomes false.",
                    "Loops are useful for counters, lists, and repeated output.",
                ],
            ),
            "activity_title": "Activity 4: Repetition Practice",
            "activity_instructions": build_activity_content(
                "Create a loop that displays five practice messages.",
                [
                    "Use a for loop from 1 to 5.",
                    "Echo Practice step and the current loop number.",
                    "After the loop, echo Finished practicing.",
                ],
                """
                <?php
                // Write your loop here
                ?>
                """,
            ),
            "activity_hint": "Use . to combine text and numbers inside echo.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\bfor\s*\(", "a for loop"),
                    required_pattern(r"\$i\s*=\s*1", "a loop that starts at 1"),
                    required_pattern(r"\$i\s*<=\s*5", "a loop condition that goes to 5"),
                    required_pattern(r"\becho\b", "an echo statement in the loop"),
                ],
                success_explanation=(
                    "This answer is correct because it uses a loop to repeat output across five practice steps."
                ),
                failure_hint=(
                    "Create a for loop that starts at 1, ends at 5, and echoes each practice step."
                ),
            ),
        },
        {
            "title": "Functions and Reusable Logic",
            "slug": "php-functions-and-reusable-logic",
            "summary": "Create functions that organize and reuse tasks.",
            "lecture_content": build_lesson_content(
                [
                    "Functions help you group instructions into reusable blocks of logic.",
                    "They make your programs easier to read because each function can focus on one clear responsibility.",
                ],
                """
                <?php
                function greet($name) {
                    echo "Hello, " . $name;
                }

                greet("Nina");
                ?>
                """,
                [
                    "function defines a reusable block of code.",
                    "Parameters pass input values into the function.",
                    "Calling a function runs the code inside it.",
                ],
            ),
            "activity_title": "Activity 5: Encouragement Function",
            "activity_instructions": build_activity_content(
                "Create a function that prints a study message.",
                [
                    "Define a function named showTopic.",
                    "Let it receive one parameter named topic.",
                    "Echo I am practicing followed by the topic.",
                    "Call the function two times with different topics.",
                ],
                """
                <?php
                function showTopic($topic) {
                    // Write your echo statement here
                }
                ?>
                """,
            ),
            "activity_hint": "A parameter works like a variable inside the function body.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"function\s+showTopic\s*\(\s*\$topic\s*\)", "the showTopic($topic) function"),
                    required_pattern(r"\becho\b", "an echo statement inside the function"),
                    required_pattern(r"showTopic\s*\(", "two calls to showTopic()", count=3),
                ],
                success_explanation=(
                    "Your answer is correct because it creates a reusable function with a parameter and calls it multiple times."
                ),
                failure_hint=(
                    "Define showTopic($topic), echo a practice message inside it, and call showTopic() twice."
                ),
            ),
        },
        {
            "title": "Arrays, Simple Problem Solving, and Final Quiz",
            "slug": "php-arrays-problem-solving-and-final-quiz",
            "summary": "Work with arrays, summarize values, and complete the final course quiz.",
            "lecture_content": build_lesson_content(
                [
                    "Arrays store multiple related values in one variable, making it easier to manage groups of data such as scores or names.",
                    "When arrays are combined with loops, you can solve beginner-friendly problems like totals, counts, and summaries.",
                ],
                """
                <?php
                $scores = [88, 76, 94, 81];
                $total = 0;

                foreach ($scores as $score) {
                    $total += $score;
                }

                echo "Total: " . $total;
                ?>
                """,
                [
                    "Arrays in PHP can be written with square brackets.",
                    "foreach is useful for reading each array item.",
                    "Breaking a problem into steps helps you code with confidence.",
                ],
            ),
            "activity_title": "Activity 6: Score Report",
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
                ?>
                """,
            ),
            "activity_hint": "count($scores) gives you the number of values in the array.",
            "activity_validation": build_activity_validation(
                [
                    required_pattern(r"\$scores\s*=\s*\[", "a $scores array"),
                    required_pattern(r"\bforeach\s*\(", "a foreach loop"),
                    required_pattern(r"total\s*\+=", "logic that adds each score to $total"),
                    required_pattern(r"\becho\b", "an echo statement for the result"),
                ],
                success_explanation=(
                    "This is correct because it stores scores in an array, loops through them, and calculates a total."
                ),
                failure_hint=(
                    "Use a $scores array, iterate with foreach, add each score to $total, and echo the result."
                ),
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
