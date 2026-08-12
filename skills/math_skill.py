from command_system.detect_math_expression import detect_math_expression

skill = {
    "name": "Math Skill",
    "description": "Handles calculations",
    "priority": 2
}

def can_handle(command):

    keywords = [
        "plus",
        "minus",
        "multiply",
        "divide",
        "calculate",
        "+",
        "-",
        "*",
        "/"
    ]

    return any(word in command for word in keywords)


def execute(command):

    return detect_math_expression(command)