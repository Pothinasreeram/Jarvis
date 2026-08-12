from skills.project_skill import can_handle, execute


tests = [
    "where is ask ai",
    "where is ask_ai",
    "find process command",
    "where is vision controller",
    "find project indexer",
    "locate assistant",
    "search for ask ai",
    "where can i find project indexer",
]


for command in tests:

    print("\n")
    print("=" * 60)
    print(f"COMMAND: {command}")
    print("=" * 60)

    print(
        "Can handle:",
        can_handle(command)
    )

    if can_handle(command):

        result = execute(command)

        print("\nRESULT:")
        print(result)