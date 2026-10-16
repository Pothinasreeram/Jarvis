"""
Taskmaster & To-Do Directives Voice Skill for J.A.R.V.I.S.
Handles voice requests to add, list, complete, and manage task directives.
"""

import re
from system_layer.todo_controller import (
    add_task,
    complete_task,
    list_tasks_summary,
    clear_completed_tasks,
)

skill = {
    "name": "Taskmaster Skill",
    "priority": 25,
}

TRIGGER_KEYWORDS = [
    "add task",
    "add a task",
    "new task",
    "add todo",
    "add to-do",
    "my tasks",
    "pending tasks",
    "what are my tasks",
    "show tasks",
    "list tasks",
    "to-do list",
    "complete task",
    "mark task as done",
    "finish task",
    "clear completed tasks",
]


def can_handle(command: str) -> bool:
    cmd = command.lower().strip()
    if any(kw in cmd for kw in TRIGGER_KEYWORDS):
        return True
    if any(w in cmd for w in ["task", "todo", "directive"]) and any(a in cmd for a in ["add", "show", "list", "complete", "finish", "done", "clear"]):
        return True
    return False


def execute(command: str) -> str:
    cmd = command.lower().strip()

    # 1. Clear completed
    if "clear" in cmd and ("completed" in cmd or "done" in cmd or "tasks" in cmd):
        return clear_completed_tasks()

    # 2. Add task (checked before complete to handle tasks like 'add task finish resume')
    if any(w in cmd for w in ["add", "new", "create", "log"]) and any(w in cmd for w in ["task", "todo", "directive"]):
        match = re.search(r'(?:add|new|create|log)\s+(?:a\s+)?(?:task|todo|directive)(?:\s+to)?(?:\s+that)?(?:\s*:)?\s+(.+)', cmd)
        if match:
            task_text = match.group(1).strip()
            return add_task(task_text)
        else:
            words = cmd.split()
            if len(words) > 2:
                return add_task(" ".join(words[2:]))

    # 3. Complete task
    if any(w in cmd for w in ["complete", "finish", "done", "mark"]):
        # Extract task identifier (number or name)
        match = re.search(r'(?:task|todo|directive)\s+(?:number\s+)?(\d+|[\w\s]+)', cmd)
        if match:
            ident = match.group(1).replace("as done", "").replace("as completed", "").strip()
            return complete_task(ident)
        # Fallback simple split
        words = cmd.split()
        return complete_task(words[-1])

    # 4. List tasks (default)
    return list_tasks_summary()
