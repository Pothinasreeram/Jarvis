from skills.file_skill import can_handle


tests = [
    "find my pdf",
    "find my resume",
    "find screenshot",
    "find process command",
    "find ask ai",
    "find project indexer",
    "where is vision controller",
]


print("\nFILE SKILL ROUTING TEST")
print("=" * 60)


for command in tests:

    result = can_handle(command)

    print(
        f"{command:<30} -> "
        f"{result}"
    )