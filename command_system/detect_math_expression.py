import re
import ast
import operator as op
from datetime import datetime

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def evaluate_expression(expr):
    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                _eval(node.left),
                _eval(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](
                _eval(node.operand)
            )
        else:
            raise TypeError(node)

    node = ast.parse(expr, mode='eval').body
    return _eval(node)

def detect_math_expression(command):
    command = command.lower()

    # Normalize spoken words to math operators
    replacements = [
        ("multiplied by", "*"),
        ("multiply by", "*"),
        ("times", "*"),
        ("divided by", "/"),
        ("divide by", "/"),
        ("plus", "+"),
        ("minus", "-"),
        ("x", "*"),
    ]
    for word, symbol in replacements:
        command = command.replace(word, symbol)

    # Extract only math characters from sentence
    expression = re.findall(r"[\d\.\+\-\*/\(\)]+", command)

    if not expression:
        return None

    expression = "".join(expression)

    try:
        result = evaluate_expression(expression)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"The result is {result}"
    except:
        return None
def detect_time_date(command):
    command = command.lower()

    if "time" in command:
        now = datetime.now().strftime("%I:%M %p")
        return f"The current time is {now}"

    if "date" in command or "today" in command or "day" in command:
        today = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {today}"

    return None    